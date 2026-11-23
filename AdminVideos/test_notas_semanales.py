"""Regresión del pin semanal de notas (sin navegador)."""
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from AdminVideos.models import MenuDia, MenuNota, NotaSemanal
from AdminVideos.views import asegurar_notas_semanales


class NotaSemanalTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="nota_test", password="testpass")
        self.client.force_login(self.usuario)
        self.lunes = date(2026, 11, 23)
        self.menu = MenuDia.objects.create(propietario=self.usuario, fecha=self.lunes)
        self.nota = MenuNota.objects.create(
            menu=self.menu, momento="almuerzo", texto="No como en casa",
            cuenta_como_programada=True,
        )

    def fijar(self, nota):
        response = self.client.post(reverse("ajax_fijar_nota", args=[nota.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        return response.json()["fijado"]

    def test_pin_genera_siguientes_lunes_sin_duplicar(self):
        self.assertTrue(self.fijar(self.nota))
        fechas = [self.lunes, self.lunes + timedelta(days=7)]
        asegurar_notas_semanales(self.usuario, fechas)
        asegurar_notas_semanales(self.usuario, fechas)
        notas = MenuNota.objects.filter(nota_semanal__isnull=False)
        self.assertEqual(notas.count(), 2)
        self.assertEqual(NotaSemanal.objects.count(), 1)
        self.assertTrue(all(n.cuenta_como_programada for n in notas))

    def test_desfijar_conserva_nota_visible_y_quita_repeticion(self):
        self.fijar(self.nota)
        siguiente = self.lunes + timedelta(days=7)
        asegurar_notas_semanales(self.usuario, [self.lunes, siguiente])
        segunda = MenuNota.objects.get(menu__fecha=siguiente)
        self.assertFalse(self.fijar(segunda))
        segunda.refresh_from_db()
        self.assertIsNone(segunda.nota_semanal_id)
        self.assertFalse(MenuNota.objects.filter(pk=self.nota.pk).exists())
        self.assertEqual(NotaSemanal.objects.count(), 0)
        asegurar_notas_semanales(self.usuario, [self.lunes, siguiente])
        self.assertEqual(MenuNota.objects.count(), 1)

    def test_editar_fijada_actualiza_todas_las_semanas(self):
        self.fijar(self.nota)
        siguiente = self.lunes + timedelta(days=7)
        asegurar_notas_semanales(self.usuario, [self.lunes, siguiente])
        response = self.client.post(reverse("ajax_editar_nota", args=[self.nota.pk]), {
            "texto": "Almuerzo afuera", "cuenta_como_programada": "", 
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(MenuNota.objects.values_list("texto", flat=True)), {"Almuerzo afuera"})
        self.assertFalse(NotaSemanal.objects.get().cuenta_como_programada)
        self.assertFalse(MenuNota.objects.filter(cuenta_como_programada=True).exists())

    def test_borrar_fijada_quita_recurrencia(self):
        self.fijar(self.nota)
        asegurar_notas_semanales(self.usuario, [self.lunes, self.lunes + timedelta(days=7)])
        response = self.client.post(reverse("ajax_borrar_nota", args=[self.nota.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MenuNota.objects.count(), 0)
        self.assertEqual(NotaSemanal.objects.count(), 0)

    def test_nota_semanal_no_programada_no_colorea_dia(self):
        from AdminVideos.views import obtener_platos_dia_x_dia
        self.nota.cuenta_como_programada = False
        self.nota.save(update_fields=["cuenta_como_programada"])
        self.fijar(self.nota)
        siguiente = self.lunes + timedelta(days=7)
        asegurar_notas_semanales(self.usuario, [siguiente])
        _, dias_programados, dias_completos, notas = obtener_platos_dia_x_dia(
            self.usuario, [self.lunes, siguiente], set()
        )
        self.assertFalse(dias_programados)
        self.assertFalse(dias_completos)
        self.assertFalse(notas[siguiente]["almuerzo"][0]["cuenta_como_programada"])

    def test_no_permite_fijar_nota_de_otro_usuario(self):
        otro = User.objects.create_user(username="nota_otro", password="12345")
        self.client.force_login(otro)
        response = self.client.post(reverse("ajax_fijar_nota", args=[self.nota.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(NotaSemanal.objects.count(), 0)
