from django.contrib.auth.models import BaseUserManager
#from autofarmapage.models import is_active, is_admin, is_staff


class UserManager(BaseUserManager):
    def create_user(self, rut, tipo_empleado=None ,password=None, is_active=True, is_staff=False, is_admin=False, email=None):
        from .models import Persona, TipoEmpleado
        if password is None:
            password = self.crear_contrasenna(rut)
        if not rut:
            raise ValueError("Usuario debe tener un rut")
        if not password:
            raise ValueError("Usuario debe tener una contraseña")
        persona = Persona.objects.get(rut=rut)
        if tipo_empleado is not None:
            tipo_emp = TipoEmpleado.objects.get(id_tipo_empleado=tipo_empleado)
        else:
            tipo_emp = None
            
        if persona is not None:
            user_obj = self.model(
                rut=persona
            )
        else:
            raise ValueError("El rut no existe en nuestros registros")

        #user_obj = self.model(
         #   rut=self.model.normalize_username(rut)
        #)
        
        user_obj.set_password(password)
        user_obj.id_tipo_empleado = tipo_emp
        user_obj.habilitado = is_active
        user_obj.admin = is_admin
        user_obj.staff = is_staff
        user_obj.email = email
        user_obj.save(using=self._db)
        return user_obj

    def create_superuser(self, rut, password):
        user_obj = self.create_user(
            rut,
            tipo_empleado=3,
            password=password,
            is_active=True,
            is_staff=True,
            is_admin=True
        )
        user_obj.save(using=self._db)
        return user_obj

    #crea la contraseña inicial
    def crear_contrasenna(self, rut):
        password = rut[0:4]
        return password
