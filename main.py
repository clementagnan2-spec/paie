"""
App de Paie Burkina Faso - Kivy
Génère les bulletins de paie et le bordereau d'écriture comptable.
Le bordereau comptable est payant : déblocage via Orange Money
(paiement à l'unité, par bordereau généré).
"""

import json
import os
import threading
import time
import uuid

import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.screenmanager import Screen, ScreenManager

from payroll_engine import Employee, calcul_bulletin, calcul_bordereau_comptable

# ----------------------------------------------------------------------
# CONFIGURATION - à adapter avant compilation
# ----------------------------------------------------------------------
BACKEND_URL = "https://TON-BACKEND.onrender.com"   # <-- remplace par l'URL de ton backend déployé
PRIX_BORDEREAU_FCFA = 500                           # prix par bordereau généré

# MODE TEST : passe à False une fois le backend + LigdiCash configurés.
# En mode test, le paiement est simulé (pas d'appel réseau, pas de vrai débit).
MODE_TEST = True

DATA_FILE = os.path.join(App.get_running_app().user_data_dir, "employes.json") \
    if App.get_running_app() else "employes.json"

KV = """
ScreenManager:
    ListeEmployesScreen:
    FormEmployeScreen:
    BulletinsScreen:
    PaiementScreen:
    BordereauScreen:

<ListeEmployesScreen>:
    name: "liste"
    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10

        Label:
            text: "Paie Burkina Faso"
            font_size: 24
            size_hint_y: None
            height: 50
            bold: True

        Label:
            text: "[color=ff6f00]MODE TEST - paiement simulé[/color]" if app.mode_test_actif else ""
            markup: True
            size_hint_y: None
            height: 25 if app.mode_test_actif else 0

        ScrollView:
            BoxLayout:
                id: liste_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: 5

        BoxLayout:
            size_hint_y: None
            height: 50
            spacing: 10
            Button:
                text: "+ Ajouter un salarié"
                on_release: app.root.get_screen("form").reset_form(); app.root.current = "form"
            Button:
                text: "Voir bulletins"
                on_release: app.root.current = "bulletins"
            Button:
                text: "Bordereau comptable"
                on_release: app.root.current = "bordereau"

<FormEmployeScreen>:
    name: "form"
    nom: nom_input
    prenom: prenom_input
    classification: classification_input
    salaire_base: salaire_input
    heure_sup: heuresup_input
    sursalaire: sursalaire_input
    gratification: gratif_input
    indemnite_caisse: caisse_input
    indemnite_logement: logement_input
    indemnite_fonction: fonction_input
    indemnite_transport: transport_input
    nb_charges: charges_input
    retenue_avance: avance_input

    ScrollView:
        BoxLayout:
            orientation: "vertical"
            padding: 20
            spacing: 8
            size_hint_y: None
            height: self.minimum_height

            Label:
                text: "Nouveau salarié"
                font_size: 20
                size_hint_y: None
                height: 40

            Label:
                text: "Nom"
                size_hint_y: None
                height: 25
            TextInput:
                id: nom_input
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Prénom"
                size_hint_y: None
                height: 25
            TextInput:
                id: prenom_input
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Classification (CADRE ou AUTRE)"
                size_hint_y: None
                height: 25
            TextInput:
                id: classification_input
                text: "AUTRE"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Salaire de base (FCFA)"
                size_hint_y: None
                height: 25
            TextInput:
                id: salaire_input
                input_filter: "float"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Heures supplémentaires (FCFA)"
                size_hint_y: None
                height: 25
            TextInput:
                id: heuresup_input
                input_filter: "float"
                text: "0"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Sursalaire (FCFA)"
                size_hint_y: None
                height: 25
            TextInput:
                id: sursalaire_input
                input_filter: "float"
                text: "0"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Gratification (FCFA)"
                size_hint_y: None
                height: 25
            TextInput:
                id: gratif_input
                input_filter: "float"
                text: "0"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Indemnité de caisse (FCFA)"
                size_hint_y: None
                height: 25
            TextInput:
                id: caisse_input
                input_filter: "float"
                text: "0"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Indemnité de logement (FCFA)"
                size_hint_y: None
                height: 25
            TextInput:
                id: logement_input
                input_filter: "float"
                text: "0"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Indemnité de fonction (FCFA)"
                size_hint_y: None
                height: 25
            TextInput:
                id: fonction_input
                input_filter: "float"
                text: "0"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Indemnité de transport (FCFA)"
                size_hint_y: None
                height: 25
            TextInput:
                id: transport_input
                input_filter: "float"
                text: "0"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Nombre de personnes à charge (0-4+)"
                size_hint_y: None
                height: 25
            TextInput:
                id: charges_input
                input_filter: "int"
                text: "0"
                size_hint_y: None
                height: 40
                multiline: False

            Label:
                text: "Retenue avance/prêt (FCFA)"
                size_hint_y: None
                height: 25
            TextInput:
                id: avance_input
                input_filter: "float"
                text: "0"
                size_hint_y: None
                height: 40
                multiline: False

            BoxLayout:
                size_hint_y: None
                height: 50
                spacing: 10
                padding: (0, 10, 0, 0)
                Button:
                    text: "Annuler"
                    on_release: app.root.current = "liste"
                Button:
                    text: "Enregistrer"
                    on_release: root.enregistrer()

<BulletinsScreen>:
    name: "bulletins"
    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10
        Label:
            text: "Bulletins de paie"
            font_size: 22
            size_hint_y: None
            height: 40
        ScrollView:
            BoxLayout:
                id: bulletins_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: 15
        Button:
            text: "Retour"
            size_hint_y: None
            height: 50
            on_release: app.root.current = "liste"

<BordereauScreen>:
    name: "bordereau"
    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10
        Label:
            text: "Bordereau d'écriture comptable"
            font_size: 20
            size_hint_y: None
            height: 40
        Label:
            id: apercu_label
            text: "Génère un bordereau pour voir un aperçu (totaux uniquement).\\nLe détail complet est débloqué après paiement Orange Money."
            size_hint_y: None
            height: 80
            text_size: self.width, None
        ScrollView:
            BoxLayout:
                id: bordereau_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: 5
        BoxLayout:
            size_hint_y: None
            height: 50
            spacing: 10
            Button:
                text: "Retour"
                on_release: app.root.current = "liste"
            Button:
                text: "Payer et débloquer (Orange Money)"
                on_release: app.root.get_screen("paiement").preparer_paiement(); app.root.current = "paiement"

<PaiementScreen>:
    name: "paiement"
    statut_label: statut_label
    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 15
        Label:
            text: "Paiement Orange Money"
            font_size: 22
            size_hint_y: None
            height: 40
        Label:
            id: instructions_label
            text: ""
            size_hint_y: None
            height: 150
            text_size: self.width, None
        Label:
            text: "Numéro Orange Money"
            size_hint_y: None
            height: 25
        TextInput:
            id: numero_input
            hint_text: "Ex: 70 12 34 56"
            input_filter: "int"
            size_hint_y: None
            height: 40
            multiline: False
        Label:
            id: statut_label
            text: ""
            size_hint_y: None
            height: 60
            text_size: self.width, None
        Button:
            text: "Initier le paiement"
            size_hint_y: None
            height: 50
            on_release: root.initier_paiement()
        Button:
            text: "Retour"
            size_hint_y: None
            height: 50
            on_release: app.root.current = "bordereau"
"""


class ListeEmployesScreen(Screen):
    def on_pre_enter(self):
        self.rafraichir()

    def rafraichir(self):
        box = self.ids.liste_box
        box.clear_widgets()
        app = App.get_running_app()
        from kivy.uix.label import Label
        if not app.employes:
            box.add_widget(Label(text="Aucun salarié. Ajoute-en un.", size_hint_y=None, height=40))
        for i, e in enumerate(app.employes):
            box.add_widget(Label(
                text=f"{e.nom} {e.prenom} - {e.salaire_base:,.0f} FCFA",
                size_hint_y=None, height=35
            ))


class FormEmployeScreen(Screen):
    def reset_form(self):
        for field_id in ["nom", "prenom"]:
            self.ids[field_id].text = ""
        self.ids["classification"].text = "AUTRE"
        for field_id in ["salaire_base", "heure_sup", "sursalaire", "gratification",
                          "indemnite_caisse", "indemnite_logement", "indemnite_fonction",
                          "indemnite_transport", "retenue_avance"]:
            self.ids[field_id].text = "0"
        self.ids["nb_charges"].text = "0"

    def enregistrer(self):
        app = App.get_running_app()

        def f(field_id):
            try:
                return float(self.ids[field_id].text or 0)
            except ValueError:
                return 0.0

        emp = Employee(
            nom=self.ids["nom"].text.strip(),
            prenom=self.ids["prenom"].text.strip(),
            classification=self.ids["classification"].text.strip().upper() or "AUTRE",
            salaire_base=f("salaire_base"),
            heure_sup=f("heure_sup"),
            sursalaire=f("sursalaire"),
            gratification=f("gratification"),
            indemnite_caisse=f("indemnite_caisse"),
            indemnite_logement=f("indemnite_logement"),
            indemnite_fonction=f("indemnite_fonction"),
            indemnite_transport=f("indemnite_transport"),
            nb_charges=int(f("nb_charges")),
            retenue_avance=f("retenue_avance"),
        )
        app.employes.append(emp)
        app.sauvegarder_employes()
        self.manager.current = "liste"


class BulletinsScreen(Screen):
    def on_pre_enter(self):
        box = self.ids.bulletins_box
        box.clear_widgets()
        app = App.get_running_app()
        from kivy.uix.label import Label
        for e in app.employes:
            b = calcul_bulletin(e)
            texte = (
                f"[b]{b['nom']} {b['prenom']}[/b]\n"
                f"Rémunération totale : {b['Q_remuneration_totale']:,.0f} FCFA\n"
                f"CNSS salarié : {b['S_cnss_salarie']:,.0f} FCFA\n"
                f"IUTS : {b['AD_iuts_net']:,.0f} FCFA\n"
                f"[color=2e7d32][b]Net à payer : {b['AH_net_percu']:,.0f} FCFA[/b][/color]"
            )
            lbl = Label(text=texte, markup=True, size_hint_y=None, height=140,
                        text_size=(Window.width - 40, None))
            box.add_widget(lbl)


class BordereauScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        box = self.ids.bordereau_box
        box.clear_widgets()
        from kivy.uix.label import Label

        if not app.employes:
            box.add_widget(Label(text="Ajoute des salariés d'abord.", size_hint_y=None, height=40))
            return

        bulletins = [calcul_bulletin(e) for e in app.employes]
        bordereau = calcul_bordereau_comptable(bulletins)
        app.dernier_bordereau = bordereau  # gardé en mémoire pour l'export après paiement

        if app.bordereau_paye:
            for section, titre in [("debit_1", "DÉBIT"), ("credit_1", "CRÉDIT")]:
                box.add_widget(Label(text=f"[b]{titre}[/b]", markup=True, size_hint_y=None, height=30))
                for ligne in bordereau[section]:
                    box.add_widget(Label(
                        text=f"{ligne['compte']} - {ligne['libelle']} : {ligne['montant']:,.0f} FCFA",
                        size_hint_y=None, height=28, text_size=(Window.width - 40, None)
                    ))
            box.add_widget(Label(
                text=f"[b]GRAND TOTAL : {bordereau['grand_total_debit']:,.0f} FCFA[/b]",
                markup=True, size_hint_y=None, height=35
            ))
        else:
            box.add_widget(Label(
                text=f"Total général (aperçu) : {bordereau['grand_total_debit']:,.0f} FCFA\n\n"
                     f"Paie {PRIX_BORDEREAU_FCFA} FCFA via Orange Money pour voir le détail complet "
                     f"des {len(bordereau['debit_1']) + len(bordereau['debit_2'])} lignes comptables.",
                size_hint_y=None, height=100, text_size=(Window.width - 40, None)
            ))


class PaiementScreen(Screen):
    reference = StringProperty("")
    en_attente = BooleanProperty(False)

    def preparer_paiement(self):
        self.reference = str(uuid.uuid4())[:8]
        self.ids.instructions_label.text = (
            f"Montant : {PRIX_BORDEREAU_FCFA} FCFA\n"
            f"Référence : {self.reference}\n\n"
            "Saisis ton numéro Orange Money puis clique sur "
            "\"Initier le paiement\". Tu recevras une notification "
            "sur ton téléphone pour valider (code USSD)."
        )
        self.statut_label.text = ""

    def initier_paiement(self):
        numero = self.ids.numero_input.text.strip()
        if not numero:
            self.statut_label.text = "[color=c62828]Entre ton numéro Orange Money.[/color]"
            self.statut_label.markup = True
            return

        self.statut_label.markup = True

        if MODE_TEST:
            self.statut_label.text = ("[color=1565c0]MODE TEST : simulation du paiement "
                                       "(aucun vrai débit)...[/color]")
            Clock.schedule_once(lambda dt: self._paiement_confirme(), 2)
            return

        self.statut_label.text = "[color=1565c0]Envoi de la demande de paiement...[/color]"
        threading.Thread(target=self._payer_en_arriere_plan, args=(numero,), daemon=True).start()

    def _payer_en_arriere_plan(self, numero):
        try:
            resp = requests.post(
                f"{BACKEND_URL}/create-payment",
                json={
                    "phone": numero,
                    "amount": PRIX_BORDEREAU_FCFA,
                    "reference": self.reference,
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as ex:
            Clock.schedule_once(lambda dt: self._set_statut(
                f"[color=c62828]Erreur de connexion au serveur de paiement : {ex}[/color]"))
            return

        Clock.schedule_once(lambda dt: self._set_statut(
            "[color=1565c0]Paiement en cours. Compose le code USSD si demandé, "
            "puis patiente...[/color]"))

        # Vérification du statut toutes les 5 secondes, jusqu'à 3 minutes
        for _ in range(36):
            time.sleep(5)
            try:
                r = requests.get(f"{BACKEND_URL}/check-payment/{self.reference}", timeout=10)
                statut = r.json().get("status")
            except Exception:
                continue
            if statut == "paid":
                Clock.schedule_once(lambda dt: self._paiement_confirme())
                return
            elif statut == "failed":
                Clock.schedule_once(lambda dt: self._set_statut(
                    "[color=c62828]Paiement échoué ou annulé.[/color]"))
                return

        Clock.schedule_once(lambda dt: self._set_statut(
            "[color=c62828]Délai dépassé. Réessaie.[/color]"))

    def _set_statut(self, texte):
        self.statut_label.text = texte

    def _paiement_confirme(self):
        app = App.get_running_app()
        app.bordereau_paye = True
        self.statut_label.text = "[color=2e7d32]Paiement confirmé ! Redirection...[/color]"
        Clock.schedule_once(lambda dt: setattr(self.manager, "current", "bordereau"), 1.5)


class PaieApp(App):
    def build(self):
        self.employes = []
        self.bordereau_paye = False
        self.dernier_bordereau = None
        self.mode_test_actif = MODE_TEST
        self.data_file = os.path.join(self.user_data_dir, "employes.json")
        self.charger_employes()
        return Builder.load_string(KV)

    def sauvegarder_employes(self):
        data = [e.__dict__ for e in self.employes]
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def charger_employes(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, encoding="utf-8") as f:
                data = json.load(f)
            self.employes = [Employee(**d) for d in data]


if __name__ == "__main__":
    PaieApp().run()
