import unittest

import numpy as np

from tfm_data.evaluation.pm10_bootstrap import moving_block_indices, resampled_differences


class TestPm10BlockBootstrap(unittest.TestCase):
    def test_bloques_consecutivos_sin_envolver_y_semilla_reproducible(self):
        indices = moving_block_indices(10, 3, 100, 42)
        self.assertEqual(indices.shape, (100, 10))
        np.testing.assert_array_equal(indices, moving_block_indices(10, 3, 100, 42))
        self.assertGreaterEqual(indices.min(), 0)
        self.assertLess(indices.max(), 10)
        for start in (0, 3, 6):
            np.testing.assert_array_equal(np.diff(indices[:, start:start + 3], axis=1), np.ones((100, 2)))

    def test_pondera_por_observaciones_y_conserva_huecos(self):
        indices = np.array([[0, 1, 2], [1, 1, 0]])
        differences, counts = resampled_differences([3, 9, 0], [3, 1, 0], indices)
        np.testing.assert_allclose(differences, [3, 4.2])
        np.testing.assert_array_equal(counts, [4, 5])

    def test_agregacion_de_estaciones_respeta_las_mismas_fechas(self):
        indices = moving_block_indices(4, 2, 20, 42)
        totals_a, counts_a = np.array([1, 2, 3, 4]), np.ones(4)
        totals_b, counts_b = np.array([4, 0, 2, 1]), np.array([1, 0, 1, 1])
        a, na = resampled_differences(totals_a, counts_a, indices)
        b, nb = resampled_differences(totals_b, counts_b, indices)
        total, count = resampled_differences(totals_a + totals_b, counts_a + counts_b, indices)
        np.testing.assert_allclose(total, (a * na + b * nb) / (na + nb))
        np.testing.assert_array_equal(count, na + nb)

    def test_rechaza_configuracion_y_replicas_sin_datos(self):
        for length, replicas in ((0, 100), (5, 100), (2, 1)):
            with self.assertRaises(ValueError):
                moving_block_indices(4, length, replicas, 42)
        with self.assertRaises(ValueError):
            resampled_differences([0, 0], [0, 0], np.array([[0, 1]]))
        with self.assertRaises(ValueError):
            resampled_differences([1, 0], [0, 1], np.array([[0, 1]]))


if __name__ == "__main__":
    unittest.main()
