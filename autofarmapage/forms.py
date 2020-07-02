from django import forms
from django.forms import Select
from autofarmapage.models import Usuario, Persona, Region
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):

    class Meta:
        model = Usuario
        fields = ['rut', 'password']
        labels = {
            'rut': 'Usuario',
            'password': 'Contraseña'
        }

"""class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = (
            'rut',
            'nombres',
            'apellido_paterno',
            'apellido_materno',
            'telefono',
            'correo_electronico',
            'direccion',
            'id_comuna',
            'id_centro',
        )
    region = forms.ModelChoiceField(
        queryset=Region.objects.all().only("nombre_region"),
        widget=Select(attrs={'class': 'nombre_region'})
    )"""


class EditarForm(forms.ModelForm):

    class Meta:
        model = Persona
        fields = ('rut', 'nombres', 'apellido_paterno', 'apellido_materno', 'telefono', 'correo_electronico', 'direccion', 'id_comuna', 'id_centro',)
        labels = {
            'rut': 'rut', 
            'nombres': 'nombres',
            'apellido_patero': 'Apellido Paterno',
            'apellido_materno': 'Apellido Materno', 
            'telefono': 'telefono', 
            'correo_electronico': 'correo_electronico', 
            'direccion': 'direccion',
            'id_comuna': 'id_comuna',
            'id_centro': 'id_centro'
        }


class RegistrarForm(forms.ModelForm):

    class Meta:
        model = Persona
        fields = ('rut', 'nombres', 'apellido_paterno', 'apellido_materno', 'telefono', 'correo_electronico', 'direccion', 'id_comuna', 'id_centro')