# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from .managers import UserManager


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)

class Caducado(models.Model):
    cantidad = models.BigIntegerField()
    codigo = models.OneToOneField('Medicamento', models.DO_NOTHING, db_column='codigo', primary_key=True, related_name="cad_codigo")
    id_centro = models.ForeignKey('CentroSalud', models.DO_NOTHING, db_column='id_centro')

    class Meta:
        managed = False
        db_table = 'caducado'
        unique_together = (('codigo', 'id_centro'),)


class CentroSalud(models.Model):
    id_centro = models.BigIntegerField(primary_key=True)
    nombre_centro = models.CharField(max_length=250)
    direccion = models.CharField(max_length=100)
    id_comuna = models.ForeignKey('Comuna', models.DO_NOTHING, db_column='id_comuna')
    id_tipo = models.ForeignKey('TipoCentroSalud', models.DO_NOTHING, db_column='id_tipo')

    class Meta:
        managed = False
        db_table = 'centro_salud'


class ColaboradorFarmacia(models.Model):
    rut = models.OneToOneField('Persona', models.DO_NOTHING, db_column='rut', primary_key=True)

    class Meta:
        managed = False
        db_table = 'colaborador_farmacia'


class Componente(models.Model):
    nombre_componente = models.CharField(max_length=100)
    medida_componente = models.BigIntegerField()
    id_tipo_componente = models.ForeignKey('TipoComponente', models.DO_NOTHING, db_column='id_tipo_componente')
    id_medida = models.ForeignKey('MedidaComponente', models.DO_NOTHING, db_column='id_medida')
    codigo = models.ForeignKey('Medicamento', models.DO_NOTHING, db_column='codigo')
    id_componente = models.BigIntegerField(primary_key=True)
    
    class Meta:
        managed = False
        db_table = 'componente'


class Comuna(models.Model):
    id_comuna = models.BigIntegerField(primary_key=True)
    nombre_comuna = models.CharField(max_length=50)
    id_region = models.ForeignKey('Region', models.DO_NOTHING, db_column='id_region')

    class Meta:
        managed = False
        db_table = 'comuna'


class DetalleReceta(models.Model):
    posologia = models.CharField(max_length=250)
    duracion_tratamiento = models.BigIntegerField(blank=True, null=True)
    dosis_diaria = models.BigIntegerField(blank=True, null=True)
    id_tipo_tratamiento = models.ForeignKey('TipoTratamiento', models.DO_NOTHING, db_column='id_tipo_tratamiento')
    id_receta = models.ForeignKey('Receta', models.DO_NOTHING, db_column='id_receta')
    codigo = models.OneToOneField('Medicamento', models.DO_NOTHING, db_column='codigo', primary_key=True)
    id_medida_t = models.ForeignKey('MedidaTiempo', models.DO_NOTHING, db_column='id_medida_t')

    class Meta:
        managed = False
        db_table = 'detalle_receta'
        unique_together = (('codigo', 'id_receta'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    action_flag = models.IntegerField()
    change_message = models.TextField(blank=True, null=True)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user_id = models.CharField(max_length=8)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField(blank=True, null=True)
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class EntregaMedicamento(models.Model):
    id_entrega = models.BigIntegerField(primary_key=True)
    fecha_entrega = models.DateField()
    cantidad = models.BigIntegerField()
    codigo = models.ForeignKey(DetalleReceta, models.DO_NOTHING, db_column='codigo', related_name='+')
    id_receta = models.ForeignKey(DetalleReceta, models.DO_NOTHING, db_column='id_receta', related_name='+')
    rut_col_farmacia = models.ForeignKey(ColaboradorFarmacia, models.DO_NOTHING, db_column='rut_col_farmacia')
    #id_tipo_entrega = models.ForeignKey(TipoEntrega, models.DO_NOTHING, db_column='id_tipo_entrega')

    class Meta:
        managed = False
        db_table = 'entrega_medicamento'


class Medicamento(models.Model):
    codigo = models.BigIntegerField(primary_key=True)
    nombre_medicamento = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=250, blank=True, null=True)
    fabricante = models.CharField(max_length=100)
    id_tipo_med = models.ForeignKey('TipoMedicamento', models.DO_NOTHING, db_column='id_tipo_med')

    class Meta:
        managed = False
        db_table = 'medicamento'


class Medico(models.Model):
    rut = models.OneToOneField('Persona', models.DO_NOTHING, db_column='rut', primary_key=True)

    class Meta:
        managed = False
        db_table = 'medico'


class MedidaComponente(models.Model):
    id_medida = models.BigIntegerField(primary_key=True)
    medida = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'medida_componente'

class MedidaTiempo(models.Model):
    id_medida_t = models.BigIntegerField(primary_key=True)
    nombre_med_tiempo = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'medida_tiempo'

class Persona(models.Model):
    rut = models.CharField(primary_key=True, max_length=8)
    dv = models.CharField(max_length=1)
    nombres = models.CharField(max_length=50)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    telefono = models.BigIntegerField()
    correo_electronico = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=50)
    id_comuna = models.ForeignKey(Comuna, models.DO_NOTHING, db_column='id_comuna')
    id_centro = models.ForeignKey(CentroSalud, models.DO_NOTHING, db_column='id_centro')
    rut_tutor = models.ForeignKey('TutorPaciente', models.DO_NOTHING, db_column='rut_tutor', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'persona'


class Receta(models.Model):
    id_receta = models.BigIntegerField(primary_key=True)
    fecha_receta = models.DateField()
    rut_paciente = models.ForeignKey(Persona, models.DO_NOTHING, db_column='rut_paciente')
    rut_medico = models.ForeignKey(Medico, models.DO_NOTHING, db_column='rut_medico')

    class Meta:
        managed = False
        db_table = 'receta'


class Region(models.Model):
    id_region = models.BigIntegerField(primary_key=True)
    nombre_region = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'region'


class RegistroInformes(models.Model):
    id_informe = models.FloatField(primary_key=True)
    fecha = models.DateField()
    informe = models.BinaryField()
    id_centro = models.ForeignKey(CentroSalud, models.DO_NOTHING, db_column='id_centro')
    id_tipo_inf = models.ForeignKey('TipoInforme', models.DO_NOTHING, db_column='id_tipo_inf')

    class Meta:
        managed = False
        db_table = 'registro_informes'


class ReservaMedicamento(models.Model):
    id_reserva = models.BigIntegerField(primary_key=True)
    codigo = models.ForeignKey(DetalleReceta, models.DO_NOTHING, db_column='codigo', related_name='+')
    id_receta = models.ForeignKey(DetalleReceta, models.DO_NOTHING, db_column='id_receta', related_name='+')
    rut_col_farmacia = models.ForeignKey(ColaboradorFarmacia, models.DO_NOTHING, db_column='rut_col_farmacia')
    cantidad = models.BigIntegerField()
    fecha_reserva = models.DateField()
    entregado = models.BigIntegerField()
    stock_disponible = models.BigIntegerField()
    
    class Meta:
        managed = False
        db_table = 'reserva_medicamento'


class StockMedicamento(models.Model):
    stock = models.BigIntegerField()
    id_centro = models.OneToOneField(CentroSalud, models.DO_NOTHING, db_column='id_centro', primary_key=True)
    codigo = models.ForeignKey(Medicamento, models.DO_NOTHING, db_column='codigo')

    class Meta:
        managed = False
        db_table = 'stock_medicamento'
        unique_together = (('id_centro', 'codigo'),)


class TipoCentroSalud(models.Model):
    id_tipo = models.BigIntegerField(primary_key=True)
    nombre_tipo_centro = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tipo_centro_salud'


class TipoComponente(models.Model):
    id_tipo_componente = models.BigIntegerField(primary_key=True)
    nombre_tipo_comp = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tipo_componente'

class TipoEntrega(models.Model):
    id_tipo_entrega = models.BigIntegerField(primary_key=True)
    nombre_tipo_entrega = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tipo_entrega'

class TipoEmpleado(models.Model):
    id_tipo_empleado = models.BigIntegerField(primary_key=True)
    tipo_empleado = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'tipo_empleado'

class TipoInforme(models.Model):
    id_tipo_inf = models.BigIntegerField(primary_key=True)
    nombre_tipo_inf = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tipo_informe'

class TipoMedicamento(models.Model):
    id_tipo_med = models.BigIntegerField(primary_key=True)
    nombre_tipo_med = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'tipo_medicamento'


class TipoTratamiento(models.Model):
    id_tipo_tratamiento = models.BigIntegerField(primary_key=True)
    tipo_tratamiento = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'tipo_tratamiento'


class TutorPaciente(models.Model):
    rut = models.OneToOneField(Persona, models.DO_NOTHING, db_column='rut', primary_key=True)

    class Meta:
        managed = False
        db_table = 'tutor_paciente'

#Modelo utilizado para el User Custom
class Usuario(AbstractBaseUser):
    rut = models.OneToOneField(Persona, models.DO_NOTHING, db_column='rut', primary_key=True, unique=True)
    habilitado = models.BooleanField(default=True)
    id_tipo_empleado = models.ForeignKey(TipoEmpleado, models.DO_NOTHING, db_column='id_tipo_empleado', blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    last_login = models.DateField(blank=True, null=True)
    admin = models.BooleanField(default=True)
    staff = models.BooleanField(default=True)

    USERNAME_FIELD = 'rut'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.rut.rut

    def has_perm(self, perm, obj=None):
        return True
    
    def has_module_perms(self, app_label):
        return True

    @property
    def is_active(self):
        return self.habilitado

    @property
    def is_staff(self):
        return self.staff

    @property
    def is_admin(self):
        return self.admin

    class Meta:
        managed = False
        db_table = 'usuario'
