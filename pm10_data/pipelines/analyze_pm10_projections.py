"""Madrid exploratory PCA and LDA: training only fit, known 2023 validation."""

import json
import platform

import joblib
import numpy as np
import pandas as pd

from pm10_data.adapters.sklearn.base import backend_version
from pm10_data.adapters.sklearn.projections import LDAAdapter, PCAAdapter, ranking_metrics
from pm10_data.config import PROJECT_ROOT as ROOT
from pm10_data.evaluation.projections import choose_cut, validate_cohorts
from pm10_data.mappers.pm10_forecast import NUMERIC_FEATURES
from pm10_data.pipelines.barcelona_experiment import digest, save_csv, save_json
from pm10_data.pipelines.train_pm10_classification import classification_metrics


SOURCES = {
    'table': 'data/interim/pm10_prediction/tabla_modelos_completa.csv',
    'weather': 'data/interim/pm10_weather/tabla_pm10_meteo.csv',
    'schema': 'data/interim/pm10_weather/esquema_comparacion.json',
    'logistics': 'output/pm10_weather_validation/predicciones_validacion_2023.csv',
    'configuration': 'output/pm10_weather_validation/configuracion.json',
}


def points(rows, coordinates, partition):
    return [dict(station=str(row.codigo_estacion), name=row.NOMBRE.strip(), date=row.fecha_objetivo.strftime('%Y-%m-%d'),
                 partition=partition, elevated=int(row.pm10_elevado_objetivo),
                 x=float(coordinates[i, 0]), y=float(coordinates[i, 1]) if coordinates.shape[1] > 1 else 0.)
            for i, row in enumerate(rows.itertuples())]


def main():
    output = ROOT / 'output/experiments/projections'
    output.mkdir(parents=True, exist_ok=True)
    source_hashes = {path: digest(ROOT / path) for path in SOURCES.values()}
    protected = {p.relative_to(ROOT).as_posix(): digest(p) for p in (ROOT / 'models').rglob('*.joblib')}
    for folder in ['output/pm10_final_2024', 'output/pm10_weather_test_2025', 'output/experiments/barcelona']:
        protected.update({p.relative_to(ROOT).as_posix(): digest(p) for p in (ROOT / folder).rglob('predicciones*.csv')})
    protected.update(source_hashes)
    schema = json.loads((ROOT / SOURCES['schema']).read_text(encoding='utf-8'))
    config = json.loads((ROOT / SOURCES['configuration']).read_text(encoding='utf-8'))
    threshold = float(schema['umbral_pm10_elevado_ug_m3'])
    table = pd.read_csv(ROOT / SOURCES['table'], dtype={'codigo_estacion': str}, parse_dates=['fecha_objetivo'])
    usable = table.loc[table.fila_utilizable]
    training = usable.loc[usable.fecha_objetivo.dt.year.between(2017, 2022)].sort_values(['codigo_estacion','fecha_objetivo'])
    validation = usable.loc[usable.fecha_objetivo.dt.year.eq(2023)].sort_values(['codigo_estacion','fecha_objetivo'])
    validate_cohorts(training, validation, NUMERIC_FEATURES, list(range(2017,2023)), threshold)
    pca = PCAAdapter().fit(training[NUMERIC_FEATURES])
    details = pca.details()
    ratios = np.array(details['ratios'])
    pca_points = points(training, pca.transform(training[NUMERIC_FEATURES]), 'training') + points(validation, pca.transform(validation[NUMERIC_FEATURES]), 'validation')
    components = [dict(component=i+1, ratio=float(ratio), cumulative=float(ratios[:i+1].sum())) for i,ratio in enumerate(ratios)]
    weights = [dict(feature=feature, mean=details['means'][j], scale=details['scales'][j],
                    **{f'PC{i+1}': float(component[j]) for i,component in enumerate(details['components'])}) for j,feature in enumerate(NUMERIC_FEATURES)]
    save_csv(output/'pca_componentes.csv',pd.DataFrame(components))
    save_csv(output/'pca_pesos.csv',pd.DataFrame(weights))
    save_csv(output/'pca_proyecciones.csv',pd.DataFrame(pca_points))
    weather = pd.read_csv(ROOT/SOURCES['weather'],dtype={'codigo_estacion':str},parse_dates=['fecha_objetivo'])
    common = weather.loc[weather[schema['criterio_cohorte']]]
    train = common.loc[common.particion_meteo.eq('entrenamiento')].sort_values(['codigo_estacion','fecha_objetivo']).reset_index(drop=True)
    valid = common.loc[common.particion_meteo.eq('validacion')].sort_values(['codigo_estacion','fecha_objetivo']).reset_index(drop=True)
    base = schema['predictores_base']
    all_features = base + schema['predictores_meteorologicos']
    validate_cohorts(train, valid, all_features, [2021,2022], threshold)
    observed = valid.pm10_elevado_objetivo.astype(int)
    high = valid.pm10_t.gt(threshold)
    budget = int((high & observed.eq(0)).sum())
    if budget != config['limite_falsas_alarmas_validacion']:
        raise ValueError('La referencia de falsas alarmas ha cambiado.')
    cases = valid[['codigo_estacion','fecha_objetivo','NOMBRE','pm10_t','pm10_objetivo']].copy()
    cases['observado'] = observed
    cases['contexto'] = np.where(high,'hoy_elevado','hoy_no_elevado')
    saved = pd.read_csv(ROOT/SOURCES['logistics'],dtype={'codigo_estacion':str},parse_dates=['fecha_objetivo'])
    for _, group in saved.groupby('modelo'):
        matched = cases.merge(group,on=['codigo_estacion','fecha_objetivo'],how='outer',indicator=True,validate='one_to_one',suffixes=('','_saved'))
        if (not matched._merge.eq('both').all() or not matched.observado.eq(matched.observado_saved).all()
                or not np.allclose(matched.pm10_objetivo,matched.pm10_objetivo_saved,rtol=0,atol=1e-10)):
            raise ValueError('La comparación no comparte exactamente casos y etiquetas.')
    predictions = [saved]
    lda_reports, models, cuts = [], {'pca':pca}, {}
    for model, features in [('lda_sin_meteo',base),('lda_con_meteo',all_features)]:
        numeric = [f for f in features if f != 'codigo_estacion']
        adapter = LDAAdapter(numeric,['codigo_estacion']).fit(train[features],train.pm10_elevado_objetivo.astype(int))
        probability = adapter.predict_positive_probability(valid[features])
        cut,sweep = choose_cut(probability,observed.eq(1),high,budget)
        predictions.append(cases.assign(modelo=model,aviso=(probability>=cut).astype(int),probabilidad_elevado=probability))
        save_csv(output/f'{model}_barrido.csv',sweep)
        projection = points(train,adapter.transform(train[features]),'training') + points(valid,adapter.transform(valid[features]),'validation')
        save_csv(output/f'{model}_proyecciones.csv',pd.DataFrame(projection))
        lda_reports.append(dict(model=model,features=features,cut=cut,points=projection))
        models[model],cuts[model] = adapter,cut
    predictions = pd.concat(predictions,ignore_index=True)
    save_csv(output/'predicciones_validacion_2023.csv',predictions)
    metrics = classification_metrics(predictions,['modelo'])
    context = classification_metrics(predictions,['contexto','modelo'])
    save_csv(output/'metricas.csv',metrics)
    save_csv(output/'metricas_contexto.csv',context)
    ranking = [dict(model=model,**ranking_metrics(rows.observado,rows.probabilidad_elevado))
               for model,rows in predictions.loc[predictions.modelo.ne('persistencia')].groupby('modelo')]
    save_csv(output/'ranking.csv',pd.DataFrame(ranking))
    # Model artifacts are separate from the frozen models directory.
    joblib.dump(dict(models=models,cuts=cuts),output/'artefactos.joblib',compress=3)
    protocol = dict(scope='Madrid',pcaTraining='2017–2022',ldaTraining='2021–2022',validation=2023,threshold=threshold,
                    numericFeatures=NUMERIC_FEATURES,pcaSolver='full',pcaWhiten=False,
                    ldaParameters=dict(solver='eigen',shrinkage='auto',n_components=1,priors='training proportions'),
                    scaleFit='training only',completeCases=True,outlierClipping=False,
                    cutSelection='2023: maximize onsets, then positives, then fewer false alarms, then higher cut; same total FP budget as persistence',
                    falseAlarmBudget=budget,pcaTrainingRows=len(training),pcaValidationRows=len(validation),
                    ldaTrainingRows=len(train),ldaValidationRows=len(valid),sourceHashes=source_hashes,
                    newFinalTestEvaluation=False,versions=dict(python=platform.python_version(),sklearn=backend_version(),numpy=np.__version__,pandas=pd.__version__))
    save_json(output/'protocolo.json',protocol)
    def records(frame):
        return json.loads(frame.to_json(orient='records',double_precision=15))
    report = dict(protocol=protocol,pca=dict(components=components,weights=weights,points=pca_points,
                                           components90=int(np.searchsorted(np.cumsum(ratios),.9)+1)),
                  lda=lda_reports,metrics=records(metrics),contextMetrics=records(context),ranking=ranking,
                  logisticCuts=config['cortes_probabilidad'],originalArtifactsUnchanged=True,protectedHashes=protected)
    if any(digest(ROOT/path)!=sha for path,sha in protected.items()):
        raise ValueError('Ha cambiado un modelo o resultado protegido.')
    save_json(output/'resumen.json',report)
    print('PCA:',len(training),'entrenamiento;',len(validation),'validación;',report['pca']['components90'],'componentes para 90 %')
    print(metrics.to_string(index=False))
    print('Cortes LDA:',cuts)


if __name__=='__main__':
    main()
