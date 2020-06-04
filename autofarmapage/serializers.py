from rest_framework import serializers
from .models import Receta, Persona

class RecetaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Receta
        fields = ['id_receta', 'fecha_receta', 'rut_paciente', 'rut_medico']


class PersonaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Persona
        fields = ['rut', 'dv', 'nombres', 'apellido_paterno', 'apellido_materno', 'telefono', 'correo_electronico']        
