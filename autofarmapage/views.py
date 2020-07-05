from django.shortcuts import redirect, render
from autofarmapage.forms import LoginForm
from autofarmapage.forms import RegistrarForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as do_logout
from .models import Region, Comuna, CentroSalud, TipoEmpleado, Persona
from .connbd import ConexionBD
import cx_Oracle
from autofarmapage.forms import EditarForm
from autofarmapage.models import Caducado, Componente, DetalleReceta, EntregaMedicamento, Medicamento, MedidaComponente, MedidaTiempo, Receta, RegistroInformes, ReservaMedicamento, StockMedicamento, TipoComponente, TipoMedicamento, TipoTratamiento, TutorPaciente, Usuario
from django.contrib import messages
from autofarmapage.managers import UserManager
#from django.core.mail import send_mail
from django.core.paginator import Paginator
from .validacion import Validador
from datetime import datetime
from rest_framework import viewsets
from .serializers import RecetaSerializer, PersonaSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from autofarmapage.serializers import ReservaSerializer
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
try:
    from autofarmapage.django_asynchronous_send_mail import send_mail
except:
    from django.core.mail import send_mail
#pdf imports
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views import View

# Create your views here.

#CREA UN DICCIONARIO A PARTIR DEL RESULTADO DE UNA CONSULTA SQL
def fabricaDiccionario(cursor):
        columnNames = [d[0] for d in cursor.description]
        def createRow(*args):
            return dict(zip(columnNames, args))
        return createRow
#DEVUELVE EL RUT SIN PUNTOS, GUION NI DIGITO VERIFICADOR
def soloCuerpoRut(rut):
    rutFormateado = rut.replace('-', '')
    rutFormateado = rutFormateado.replace('.','')
    rutFormateado = rutFormateado[0 : len(rutFormateado) - 1]
    return rutFormateado

def soloDigitoVerificador(rut):
    dv = rut[-1]
    return dv
# Vista del login
def index(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        # datos para autenticar al usuario
        username = request.POST['rut']
        dv = soloDigitoVerificador(username)
        username = soloCuerpoRut(username)
        password = request.POST['password']
        # se autentica el usuario
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            # revisa el tipo de empleado que se conecta y lo redirije a su respectivo home
            if user.id_tipo_empleado == TipoEmpleado.objects.filter(id_tipo_empleado="3").get():
                # página del administrador
                return redirect('homeadmi')
            elif user.id_tipo_empleado == TipoEmpleado.objects.filter(id_tipo_empleado='2').get():
                # página del colaborador de farmacia
                return redirect('inicio-farmacia')
            elif user.id_tipo_empleado == TipoEmpleado.objects.filter(id_tipo_empleado='1').get():
                # página del médico
                return redirect('home_medico')
        else:
            #messages.error(
                #request, 'Tu nombre de usuario o contraseña no son correctos.')
            alerta = "Tu nombre de usuario o contraseña son incorrectos."
            return render(request, 'autofarmapage/index.html', {'alerta': alerta})
    return render(request, 'autofarmapage/index.html', {})

# Vista del Home del Administrador
def homeadmi(request):
    return render(request, 'autofarmapage/homeadmi.html', {})

# Vista de Agregar Usuarios del Administrador
def agregarusuario(request):
    # Querys para poblar los select del formulario de creación de persona
    #regiones = Region.objects.all()
    regiones = Region.objects.get(
        id_region=request.user.rut.id_comuna.id_region.id_region)
    #ciudades = Comuna.objects.all().order_by('nombre_comuna')
    ciudades = Comuna.objects.get(
        id_comuna=request.user.rut.id_comuna.id_comuna)
    #centro_salud = CentroSalud.objects.all().order_by('id_comuna')
    centro_salud = CentroSalud.objects.get(
        id_centro=request.user.rut.id_centro.id_centro)
    tipo_empleado = TipoEmpleado.objects.all()

    if request.method == 'POST':
        rut = request.POST['rut']
        #dv = request.POST['dv']
        #Formatea el RUT quitando puntos, guión y digito verificador
        dv = soloDigitoVerificador(rut)
        rut = soloCuerpoRut(rut)
        nombres = request.POST['nombres']
        app_paterno = request.POST['apellido_paterno']
        app_materno = request.POST['apellido_materno']
        telefono = int(request.POST['telefono'])
        email = request.POST['correo_electronico']
        direccion = request.POST['direccion']
        comuna = int(request.user.rut.id_comuna.id_comuna)
        centro_s = int(request.user.rut.id_centro.id_centro)
        id_tipo_empleado = int(request.POST['id_tipo_empleado'])
        if id_tipo_empleado == 0:
            id_tipo_empleado = None
        rut_tutor = None
        # conexión a la bd
        bd = ConexionBD()
        conn = bd.conectar()
        cursor = conn.cursor()
        realizado = cursor.var(int)
        # Llamado al procedimiento almacenado para crear persona (no crea usuario)
        cursor.callproc('pkg_crear_usuario.sp_crear_persona', [
                        rut, dv, nombres, app_paterno, app_materno, telefono, email, direccion, comuna, centro_s, rut_tutor, realizado])
        if int(realizado.getvalue()) == 1:
            #Crea el usuario
            usuario = Usuario.objects.create_user(rut, id_tipo_empleado, email=email)
            #Inserta el rut en la tabla de medicos o de colaboradores de farmacia
            if id_tipo_empleado == 1:
                #Inserta RUT en la tabla Medico
                cursor.callproc(
                    'pkg_crear_usuario.sp_ingresar_medico', [rut])
            if id_tipo_empleado == 2:
                #Inserta RUT en la tabla Colaborador_Farmacia
                cursor.callproc(
                    'pkg_crear_usuario.sp_ingresar_col_farmacia', [rut])
            #Mensaje que contiene el email
            mensaje_email = 'Tu usuario es ' + \
                usuario.rut.rut + ' .Tu contraseña es ' + rut[0:4]
            #Envío de mail con el usuario y la contraseña
            send_mail(
                'Bienvenido a Autofarma.',
                mensaje_email,
                'torpedo.page@gmail.com',
                [email],
                fail_silently=False
                )
            #Redirige a mensaje de Usuario creado exitosamente
            return redirect('exito-crear-usuario')
        elif int(realizado.getvalue()) == 0:
            # mesaje error
            messages.error(
                request, 'Se ha producido un problema y los datos no han sido almacenados. Por Favor intente nuevamente.')
    return render(request, 'autofarmapage/agregar-usuario.html', {'regiones': regiones, 'ciudades': ciudades, 'centro_salud': centro_salud, 'tipo_empleado': tipo_empleado})

#Vista de Mensaje de Usuario Creado Exitosamente (Administrador-Médico)
def guardadoUsuarioExito(request):
    return render(request, 'autofarmapage/exito-guardar-usuario.html', {})

#Vista de Mensaje de Tutor Creado Exitosamente (Administrador-Médico)
def guardadoTutorExito(request):
    return render(request, 'autofarmapage/exito-guardar-tutor.html', {})

#obtiene las personas filtradas por el id del centro
def get_personas(id_centro):
    bd = ConexionBD()
    con = bd.conectar()
    cursor = con.cursor()
    cursor.prepare("""SELECT p.nombres, p.dv, p.apellido_paterno, p.rut, NVL(t.tipo_empleado, 'Paciente') AS TIPO_EMPLEADO,
                      u.habilitado, 
                      (CASE WHEN p.rut_tutor IS NULL THEN 'Sin Registro'
                      ELSE (SELECT rut||'-'||dv FROM persona WHERE rut = p.rut_tutor)
                      END) AS RUT_TUTOR
                      FROM persona p 
                      JOIN usuario u ON p.rut=u.rut 
                      FULL OUTER JOIN tipo_empleado t ON t.id_tipo_empleado = u.id_tipo_empleado 
                      WHERE p.id_centro = :id_centro""")
    cursor.execute(None, id_centro = id_centro)   
   
    cursor.rowfactory = fabricaDiccionario(cursor)
    personas = cursor.fetchall()
    data5 ={
            'personas': personas,
        }             
    return data5

#Obtiene la persona por el criterio de busqueda    
def search_persona(id_centro, rut):
    bd = ConexionBD()
    con = bd.conectar()
    cursor = con.cursor()
    cursor.prepare("""SELECT p.nombres, p.dv, p.apellido_paterno, p.rut, NVL(t.tipo_empleado, 'Paciente') AS TIPO_EMPLEADO,
                      u.habilitado,
                      (CASE WHEN p.rut_tutor IS NULL THEN 'Sin Registro'
                      ELSE (SELECT rut||'-'||dv FROM persona WHERE rut = p.rut_tutor)
                      END) AS RUT_TUTOR
                      FROM persona p 
                      JOIN usuario u ON p.rut=u.rut 
                      FULL OUTER JOIN tipo_empleado t ON t.id_tipo_empleado = u.id_tipo_empleado 
                      WHERE p.id_centro = :id_centro AND p.rut=:rut""")
    cursor.execute(None, id_centro = id_centro, rut = rut)
    cursor.rowfactory = fabricaDiccionario(cursor)
    personas = cursor.fetchall()
    data5 ={
            'personas': personas,
        }             
    return data5  

#Vista de Listar Usuarios (Administrador)
def listarusuario(request):
    #Búsqueda del Usuario por RUT
    if request.method == 'GET':
        criterio_busqueda = request.GET.get('q')
        submitBtn = request.GET.get('submit')
        if criterio_busqueda is not None:
            id_centro = request.user.rut.id_centro.id_centro
            data5 = search_persona(id_centro, criterio_busqueda)
            return render(request, 'autofarmapage/listar-usuario.html', data5)
    #Agrega un tutor al Usuario seleccionado
    if request.method == 'POST':
        rut_tutor = request.POST['rutTutor']
        dv_tutor = soloDigitoVerificador(rut_tutor)
        rut_tutor = soloCuerpoRut(rut_tutor)
        rut_paciente = request.POST['rutPaciente']
        rut_paciente = soloCuerpoRut(rut_paciente)
        if rut_tutor == rut_paciente:
            messages.success(request, "El Rut del tutor y del usuario no pueden ser el mismo.")
        else:
            #Conexión a la bd
            bd = ConexionBD()
            con = bd.conectar()
            cursor = con.cursor()
            realizado = cursor.var(int)
            existe_tutor_tabla_persona = cursor.var(bool)
            cursor.callfunc('pkg_crear_usuario.fn_existe_persona', existe_tutor_tabla_persona, [rut_tutor])
            if existe_tutor_tabla_persona == False:
                messages.success(request, "<<¡No existe registro del rut del tutor en nuestro sistema, por favor ingresa sus datos en el apartado Crear Usuario.")
            else:
                #Procedimiento de creación del tutor
                cursor.callproc('pkg_crear_usuario.sp_crear_tutor', [
                            rut_tutor, rut_paciente, realizado])
                if realizado.getvalue() == 1:
                    #return redirect('exito-guardar-tutor')
                    messages.success(request, "<<¡TUTOR AGREGADO!>>")
                elif realizado.getvalue() == 0:
                    messages.success(request, "<<ATENCIÓN: OCURRIÓ UN ERROR>>")
    #Obtiene las personas de la base de datos que pertenecen al centro de salud del Administrador
    person = Persona.objects.filter(id_centro=request.user.rut.id_centro).order_by('rut')
    id_centro = request.user.rut.id_centro.id_centro
    data5 = get_personas(id_centro)
    return render(request, 'autofarmapage/listar-usuario.html', data5)

def cambiarCentroSalud(request):
    datos = {}
    if request.method == 'GET':
        #btn_busqueda = request.GET['submit']
        if 'submit' in request.GET:
            rut_busqueda = soloCuerpoRut(request.GET['q'])
            persona = Persona.objects.filter(rut=rut_busqueda).first()
            datos = {
                'persona': persona,
            }
    if request.method == 'POST':
        rut_persona = request.POST['rut']
        bd = ConexionBD()
        con = bd.conectar()
        cursor = con.cursor()
        resultado = cursor.var(int)
        cursor.callproc('sp_cambio_centro_salud', [rut_persona, request.user.rut.id_centro.id_centro, resultado])
        if int(resultado.getvalue()) == 1:
            msg = 'El cambio de Centro de Salud ha sido Realizado.'
            datos = {
                'msg': msg,
            }
            return render(request, 'autofarmapage/cambio_centro_salud.html', datos)
        else:
            msg = 'Se ha producido un error al procesar los datos, por favor intente nuevamente.'
            datos = {
                'msg': msg,
            }
            return render(request, 'autofarmapage/cambio_centro_salud.html', datos)
    return render(request, 'autofarmapage/cambio_centro_salud.html', datos)

#Vista de Modificar Usuario Exitosamente (Administrador)
def modificarUsuarioExito(request):
    return render(request, 'autofarmapage/exito-modificar-usuario.html', {})

#Vista Editar Persona (Administrador)
def editarPersona(request, rut):
    #Obtiene la Persona desde la base de datos
    persona = Persona.objects.filter(rut=rut)
    #Obtiene a todos los tutores (RUT) desde la base de datos
    tutor = TutorPaciente.objects.all()
    #Obtiene todas las ciudades desde la bd
    ciudades = Comuna.objects.all().order_by('nombre_comuna')
    #Obtiene todos los centros de salud desde la bd
    centro_salud = CentroSalud.objects.all().order_by('id_comuna')
    dataPerson = {
        'persona': persona,
        'tutor': tutor,
        'ciudades': ciudades,
        'centro_salud': centro_salud
    }
    #Modifica la Persona en la bd
    if request.method == 'POST':
        rut = request.POST['rut']
        rut = soloCuerpoRut(rut)
        nombres = request.POST['nombres']
        app_paterno = request.POST['apellido_paterno']
        app_materno = request.POST['apellido_materno']
        telefono = int(request.POST['telefono'])
        email = request.POST['correo_electronico']
        direccion = request.POST['direccion']
        comuna = int(request.POST['id_comuna'])
        #centro_s = int(request.POST['id_centro'])
        # lo hice para probar :(
        #sql = ('update persona '
               #'set nombres = :nombres '
               #'where rut = :rut')
        bd = ConexionBD()

        try:
            # establecer nueva conexion
            with cx_Oracle.connect(bd.bd_user,
                                   bd.bd_password,
                                   bd.dsn,
                                   encoding="UTF-8") as connection:
                # crear cursor
                with connection.cursor() as cursor:
                    # ejecutar el procedimiento
                    realizado = cursor.var(int)
                    cursor.callproc('pkg_administrar_usuario.sp_editar_persona', [
                                    rut, nombres, app_paterno, app_materno, telefono, email, direccion, comuna, realizado])

                    if int(realizado.getvalue()) == 1:
                        return redirect('exito-modificar-usuario')
                    elif int(realizado.getvalue()) == 0:
                        messages.error(
                            request, 'Se ha producido algún error, por favor intente nuevamente.')
                # commit los cambios
                    connection.commit()
        except cx_Oracle.Error as error:
            print(error)

    return render(request, 'autofarmapage/editaruser.html', dataPerson)

#Vista para deshabilitar o habilitar al usuario (Administrador)
def deshabilitarUsuario(request, rut):
    #Obtiene a la persona a habilitar/deshabilitar
    persona = Persona.objects.filter(rut=rut)
    #Form para habilitar/deshabilitar a la persona
    if request.method == 'POST':
        rut_usuario = request.POST['rutUsuario']
        opcion = int(request.POST['opcion'])
        bd = ConexionBD()
        conn = bd.conectar()
        cursor = conn.cursor()
        realizado = cursor.var(int)
        cursor.callproc('pkg_administrar_usuario.sp_des_habilitar_user', [
                        rut_usuario, opcion, realizado])
        if int(realizado.getvalue()) == 1 and opcion == 1:
            messages.success(request, 'Usuario ' +
                             rut_usuario + ' habilitado exitosamente')
        elif int(realizado.getvalue()) == 1 and opcion == 0:
            messages.success(request, 'Usuario ' +
                             rut_usuario + ' deshabilitado exitosamente')
        elif int(realizado.getvalue()) == 0:
            messages.error(
                request, 'Ha ocurrido un error al procesar los datos, por favor intenta nuevamente.')
    data = {
        'persona': persona
    }
    return render(request, 'autofarmapage/deshabilitarpage.html', data)

#Vista de Reset de la contraseña (reset completado)
def passwordResetCompleto(request):
    return render(request, 'registration/password_reset_complete_custom.html', {})

#Logout 
def logout(request):
    do_logout(request)
    return redirect('/')

##########################
# VISTA GESTIÓN FARMACIA #
##########################

#Home de Colaborador de Farmacia
def homeFarmacia(request):
    # establece el codigo de medicamento, que se guarda en la sesión del usuario
    request.session['codigo_medicamento'] = 0
    return render(request, 'autofarmapage/farmacia/inicio_bodega.html', {})

#Vista Agregar Medicamento Colaborador Farmacia
def agregarMedicamento(request):
    #Obtiene todos los tipos de medicamento desde la bd
    tipoMedicamento = TipoMedicamento.objects.all()
    #Resetea el código de medicamento a cero si ya ha sido usado durante la sesión del usuario
    request.session['codigo_medicamento'] = 0
    #Form de Registro en tabla Medicamento
    if request.method == 'POST':
        nombreMedi = request.POST['nombre_medicamento']
        descripcionMedi = request.POST['descripcion']
        fabricanteMedi = request.POST['fabricante']
        idTipoMedi = int(request.POST['id_tipo_med'])
        # conexión a bd
        bd = ConexionBD()
        con = bd.conectar()
        cursor = con.cursor()
        realizado = cursor.var(int)
        codigoMedi = cursor.var(int)
        cursor.callproc('pkg_administrar_medicamento.sp_ingresar_medicamento', [
                        nombreMedi, descripcionMedi, fabricanteMedi, idTipoMedi, realizado, codigoMedi])
        if realizado.getvalue() == 1:
            print(codigoMedi.getvalue())
            #Guarda el valor de el código de medicamento generado en el PL/SQL en la sesión del usuario, este se guarda en la bd encriptado (temporalmente)
            request.session['codigo_medicamento'] = codigoMedi.getvalue()
            new_stock = cursor.var(int)
            cursor.callproc('pkg_administrar_medicamento.sp_crear_stock_medi', [
                            request.session['codigo_medicamento'], request.user.rut.rut, new_stock])
            return redirect('agregar-componente')
        elif realizado.getvalue() == 0:
            messages.error(
                request, 'Se ha producido un error al guardar los datos, por favor intente nuevamente')
    return render(request, 'autofarmapage/agregar-medicamento.html', {'tipoMedicamento': tipoMedicamento})

#Vista para Agregar Componentes (Luego de crear Medicamento)
def agregarComponente(request):
    medidaComponente = MedidaComponente.objects.all()
    tipoComponente = TipoComponente.objects.all()
    #Obtiene el Medicamento creado a partir del código guardado en sesión
    medicamento = Medicamento.objects.get(
        codigo=request.session['codigo_medicamento'])
    #Obtiene todos los componentes ya almacenados del Medicamento
    componentes = Componente.objects.all().filter(codigo=medicamento.codigo)
    #Form para agregar o quitar Componente
    if request.method == 'POST':
        _id_componente = request.POST.get('id_componente')
        #Borra el componente si se ha presionado la opción de borrar
        if _id_componente is not None:
            delete_comp = Componente.objects.get(id_componente=_id_componente)
            delete_comp.delete()
        else:
            #Añade el componente si se ha seleccionado añadir en el formulario
            nombreComp = request.POST['nombre_componente']
            medida = request.POST['medida_componente']
            idMedida = int(request.POST['id_medida_componente'])
            idTipoComp = int(request.POST['id_tipo_componente'])
            codMedicamento = int(request.session['codigo_medicamento'])

            bd = ConexionBD()
            con = bd.conectar()
            cursor = con.cursor()

            realizado = cursor.var(int)

            cursor.callproc('pkg_administrar_medicamento.sp_add_componente', [
                            codMedicamento, nombreComp, medida, idTipoComp, idMedida, realizado])
    datos = {
        'medidaComponente': medidaComponente,
        'tipoComponente': tipoComponente,
        'componentes': componentes,
        'medicamento': medicamento
    }
    return render(request, 'autofarmapage/agregar-componente.html', datos)

#Vista de Guardado de Medicamento Exitoso
def guardadoMedicamentoExito(request):
    return render(request, 'autofarmapage/exito-guardar-medicamento.html', {})

#Vista de Listar Medicamentos
def listarMedicamento(request):
    medicamentos = Medicamento.objects.all()
    stock = StockMedicamento.objects.filter(
        id_centro=request.user.rut.id_centro.id_centro).order_by('codigo')
    caducados = Caducado.objects.filter(
        id_centro=request.user.rut.id_centro.id_centro).order_by('codigo')
    for i in stock:
        print(type(i.codigo.cad_codigo.cantidad))

    if request.method == 'GET':
        criterio_busqueda = request.GET.get('q')
        submitBtn = request.GET.get('submit')
        if criterio_busqueda is not None:
            medicamentos = Medicamento.objects.filter(
                nombre_medicamento__icontains=criterio_busqueda)
            stock = StockMedicamento.objects.filter(codigo__nombre_medicamento__icontains=criterio_busqueda).filter(
                id_centro=request.user.rut.id_centro.id_centro).order_by('codigo')
            paginador = Paginator(stock, 10)
            pagina = request.GET.get('page')
            stock = paginador.get_page(pagina)
            datos = {
                'stock': stock,
                'caducados': caducados
            }
            parametros = request.GET.copy()

            if 'page' in parametros:
                del parametros['page']

            datos['parametros'] = parametros
            return render(request, 'autofarmapage/listar-medicamento.html', datos)

    if request.method == 'POST':
        caducarBtn = request.POST.get('caducar_btn')
        # print(caducarBtn)
        if caducarBtn is not None:
            cod_medi = request.POST['codigo_med']
            print(cod_medi)
            stock_cadu = request.POST['stock_caducar']
            cod_centro = int(request.user.rut.id_centro.id_centro)
            rut_usuario = int(request.user.rut.rut)
            bd = ConexionBD()
            con = bd.conectar()
            cursor = con.cursor()

            resultado = cursor.var(int)

            cursor.callproc('pkg_administrar_medicamento.sp_caducar_medi', [
                            stock_cadu, cod_centro, cod_medi, resultado])
            print(resultado.getvalue())
            if resultado == 2:
                messages.error(
                    request, 'El Stock total es menor a la cantidad a Caducar.')
            elif resultado == 0:
                messages.error(
                    request, 'Se ha producido un error, por favor intentalo nuevamente.')

        else:

            cod_medicamento = request.POST['codigo_medicamento']
            # print(cod_medicamento)
            stock_add = request.POST['stock_aumentar']
            cod_centro = int(request.user.rut.id_centro.id_centro)
            rut_usuario = int(request.user.rut.rut)

            bd = ConexionBD()
            con = bd.conectar()
            cursor = con.cursor()

            realizado = cursor.var(int)

            cursor.callproc('pkg_administrar_medicamento.sp_aumento_stock', [
                            cod_centro, cod_medicamento, stock_add, realizado])

            # print(realizado.getvalue())
            #medicamentos = Medicamento.objects.all()
        stock = StockMedicamento.objects.filter(
            id_centro=request.user.rut.id_centro.id_centro).order_by('codigo')
        paginador = Paginator(stock, 10)
        pagina = request.GET.get('page')
        stock = paginador.get_page(pagina)
        datos = {
            'stock': stock,
            'caducados': caducados
        }
        return render(request, 'autofarmapage/listar-medicamento.html', datos)

    paginador = Paginator(stock, 10)
    pagina = request.GET.get('page')
    stock = paginador.get_page(pagina)

    datos = {
        'medicamentos': medicamentos,
        'stock': stock
    }
    parametros = request.GET.copy()

    if 'page' in parametros:
        del parametros['page']
        datos['parametros'] = parametros

    return render(request, 'autofarmapage/listar-medicamento.html', datos)

def editarMedicamento(request, codigoMed):
    medicamento = Medicamento.objects.get(codigo=codigoMed)
    return render(request, 'autofarmapage/editar-medicamento.html', {'medicamento': medicamento,})

#################################
# VISTA ENTREGA DE MEDICAMENTOS #
#################################

def inicioFarmacia(request):
    bd = ConexionBD()
    con = bd.conectar()
    cursor = con.cursor()
    respuesta = cursor.var(bool)
    respuesta = cursor.callfunc('pkg_farmacia.fn_existe_mail_no_enviado', bool, [])
    if respuesta:
        query = (
            "SELECT reserva.id_reserva AS id_reserva, "
            "med.nombre_medicamento AS nombre_medicamento, "
            "persona.rut || '-' || persona.dv AS rut_paciente, "
            "upper(persona.nombres || ' ' || persona.apellido_paterno || ' ' || persona.apellido_materno) AS nombre_paciente, "
            "persona.correo_electronico AS email "
            "FROM reserva_medicamento reserva "
            "INNER JOIN medicamento med ON reserva.codigo = med.codigo "
            "INNER JOIN receta ON reserva.id_receta = receta.id_receta "
            "INNER JOIN persona ON receta.rut_paciente = persona.rut "
            "WHERE reserva.stock_disponible = 1 "
            "AND reserva.email_enviado = 0 "
            "AND reserva.entregado = 0"
        )
        cursor.execute(query)
        cursor.rowfactory = fabricaDiccionario(cursor)
        filas = cursor.fetchall()
        for fila in filas:
            paciente = fila['NOMBRE_PACIENTE']
            rut_paciente = fila['RUT_PACIENTE']
            id_reserva = fila['ID_RESERVA']
            msg = 'Sr(a) ' + paciente + ' (' + rut_paciente + ') ' ' la reserva de medicamento N° ' + str(id_reserva) + ' se encuentra disponible para su retiro.'
            subj = 'Reserva Medicamento'
            email_paciente = fila['EMAIL']
            send_mail(
                subj,
                msg,
                'torpedo.page@gmail.com',
                [email_paciente],
                fail_silently=False,
                html = ''
            )
            cursor.callproc('pkg_farmacia.sp_marcar_mail_enviado', [id_reserva])
    return render(request, 'autofarmapage/farmacia/inicio_farmacia.html', {})

def inicioEntregas(request):
    return render(request, 'autofarmapage/farmacia/inicio_entregas.html', {})

def entregasPendientes(request):
    centroSalud = request.user.rut.id_centro.id_centro
    if request.method == 'GET':
        criterioSearch = request.GET.get('q')
        if criterioSearch is not None:
            rutSearch = soloCuerpoRut(criterioSearch)
            query = (
            "SELECT * FROM "
            "(SELECT rec.id_receta AS id, " 
            "rec.fecha_receta AS fecha, " 
            "(SELECT rut||'-'||dv FROM persona pers WHERE pers.rut = rec.rut_medico) AS rut_medico, "
            "(SELECT nombres||' '||apellido_paterno FROM persona pers WHERE pers.rut = rec.rut_medico) AS nombre_medico, "
            "(SELECT rut||'-'||dv FROM persona pers WHERE pers.rut = rec.rut_paciente) AS rut_paciente, "
            "(SELECT nombres||' '||apellido_paterno FROM persona pers WHERE pers.rut = rec.rut_paciente) AS nombre_paciente "
            "FROM receta rec INNER JOIN detalle_receta det_rec ON rec.id_receta = det_rec.id_receta "
            "INNER JOIN entrega_medicamento entr_medi ON rec.id_receta = entr_medi.id_receta "
            "INNER JOIN persona pers on rec.rut_paciente = pers.rut "
            "WHERE det_rec.id_tipo_tratamiento = 1 AND pers.id_centro = :centroSalud "
            "AND pers.rut = :rutSearch "
            "UNION "
            "SELECT rec.id_receta, " 
            "rec.fecha_receta, "
            "(SELECT rut||'-'||dv FROM persona pers WHERE pers.rut = rec.rut_medico), "
            "(SELECT nombres||' '||apellido_paterno FROM persona pers WHERE pers.rut = rec.rut_medico), "
            "(SELECT rut||'-'||dv FROM persona pers WHERE pers.rut = rec.rut_paciente), "
            "(SELECT nombres||' '||apellido_paterno FROM persona pers WHERE pers.rut = rec.rut_paciente) "
            "FROM receta rec INNER JOIN detalle_receta det_rec ON rec.id_receta = det_rec.id_receta "
            "LEFT JOIN entrega_medicamento entr_medi ON rec.id_receta = entr_medi.id_receta "
            "INNER JOIN persona pers on rec.rut_paciente = pers.rut "
            "WHERE pers.id_centro = :centroSalud "
            "AND pers.rut = :rutSearch "
            "AND entr_medi.id_receta IS NULL) "
            "ORDER BY fecha DESC " 
            )
            bd = ConexionBD()
            con = bd.conectar()
            cursor = con.cursor()
            cursor.execute(query, [centroSalud, rutSearch])
            cursor.rowfactory = fabricaDiccionario(cursor)
            filas = cursor.fetchall()
            datos = {
                'recetasPendientes' : filas,
            }
            return render(request, 'autofarmapage/farmacia/entregas_pendientes.html', datos)
    bd = ConexionBD()
    con = bd.conectar()
    cursor = con.cursor()
    query = ("SELECT * FROM "
            "(SELECT rec.id_receta AS id, " 
            "rec.fecha_receta AS fecha, " 
            "(SELECT rut||'-'||dv FROM persona pers WHERE pers.rut = rec.rut_medico) AS rut_medico, "
            "(SELECT nombres||' '||apellido_paterno FROM persona pers WHERE pers.rut = rec.rut_medico) AS nombre_medico, "
            "(SELECT rut||'-'||dv FROM persona pers WHERE pers.rut = rec.rut_paciente) AS rut_paciente, "
            "(SELECT nombres||' '||apellido_paterno FROM persona pers WHERE pers.rut = rec.rut_paciente) AS nombre_paciente "
            "FROM receta rec INNER JOIN detalle_receta det_rec ON rec.id_receta = det_rec.id_receta "
            "INNER JOIN entrega_medicamento entr_medi ON rec.id_receta = entr_medi.id_receta "
            "INNER JOIN persona pers on rec.rut_paciente = pers.rut "
            "WHERE det_rec.id_tipo_tratamiento = 1 AND pers.id_centro = :centroSalud "
            "UNION "
            "SELECT rec.id_receta, " 
            "rec.fecha_receta, "
            "(SELECT rut||'-'||dv FROM persona pers WHERE pers.rut = rec.rut_medico), "
            "(SELECT nombres||' '||apellido_paterno FROM persona pers WHERE pers.rut = rec.rut_medico), "
            "(SELECT rut||'-'||dv FROM persona pers WHERE pers.rut = rec.rut_paciente), "
            "(SELECT nombres||' '||apellido_paterno FROM persona pers WHERE pers.rut = rec.rut_paciente) "
            "FROM receta rec INNER JOIN detalle_receta det_rec ON rec.id_receta = det_rec.id_receta "
            "LEFT JOIN entrega_medicamento entr_medi ON rec.id_receta = entr_medi.id_receta "
            "INNER JOIN persona pers on rec.rut_paciente = pers.rut "
            "WHERE pers.id_centro = :centroSalud "
            "AND entr_medi.id_receta IS NULL) "
            "ORDER BY fecha DESC "  
            )
    cursor.execute(query, [centroSalud])
    cursor.rowfactory = fabricaDiccionario(cursor)
    filas = cursor.fetchall()
    datos = {
        'recetasPendientes' : filas,
    }
    return render(request, 'autofarmapage/farmacia/entregas_pendientes.html', datos)

def entregaMedicamento(request, id_receta):
    receta = Receta.objects.filter(id_receta=id_receta)
    receta_2 = Receta.objects.get(id_receta=id_receta)
    paciente = Persona.objects.get(rut=receta_2.rut_paciente.rut)
    if paciente.rut_tutor is None:
        tutor = None
    else:
        tutor = Persona.objects.get(rut=paciente.rut_tutor.rut.rut)
    datos = {}
    permanenteEntregadoAnterior = None
    bd = ConexionBD()
    con = bd.conectar()
    cursor = con.cursor()
    medicPermanente = cursor.callfunc("pkg_farmacia.fn_permanente_entrega", int, [id_receta])
    if medicPermanente == 1:
        bd = ConexionBD()
        con = bd.conectar()
        cursor = con.cursor()
        query = ("SELECT med.nombre_medicamento AS NOMBRE_MEDICAMENTO, "
                "entr.codigo AS CODIGO_MED, "
                "med.descripcion AS DESCRIPCION_MED, "
                "det.dosis_diaria, "
                "tipo_med.nombre_tipo_med AS PRESENTACION_MED, "
                "MAX(entr.fecha_entrega) AS ULTIMA_ENTREGA, "
                "MIN(entr.fecha_entrega) AS PRIMERA_ENTREGA, "
                "det.posologia AS POSOLOGIA, "
                "tipo_trat.tipo_tratamiento AS TIPO_TRATAMIENTO, "
                "NVL(st.stock, 0) AS TOTAL_STOCK, "
                "NVL(cadu.cantidad, 0) AS CANTIDAD_CADUCADO, "
                "NVL(st.stock, 0) - NVL(cadu.cantidad, 0) AS STOCK_DISPONIBLE, "
                "MAX(entr.fecha_entrega) + 30 AS PROX_ENTREGA, "
                "(CASE WHEN MAX(entr.fecha_entrega) + 30 >= sysdate then 0 ELSE 1 END) AS PUEDE_ENTREGAR "
                "FROM detalle_receta det "
                "INNER JOIN entrega_medicamento entr ON det.id_receta = entr.id_receta "
                "AND det.codigo = entr.codigo "
                "INNER JOIN medicamento med ON med.codigo = entr.codigo "
                "INNER JOIN tipo_medicamento tipo_med ON tipo_med.id_tipo_med = med.id_tipo_med "
                "INNER JOIN tipo_tratamiento tipo_trat ON tipo_trat.id_tipo_tratamiento = det.id_tipo_tratamiento "
                "INNER JOIN receta rece ON rece.id_receta = entr.id_receta "
                "INNER JOIN persona pers ON pers.rut = rece.rut_paciente "
                "INNER JOIN stock_medicamento st ON st.codigo = entr.codigo AND st.id_centro = pers.id_centro "
                "INNER JOIN caducado cadu ON cadu.codigo = entr.codigo AND cadu.id_centro = pers.id_centro "
                "WHERE det.id_receta = :id_receta "
                "GROUP BY entr.codigo, med.nombre_medicamento, det.dosis_diaria, tipo_med.nombre_tipo_med, det.posologia, "
                "med.descripcion, tipo_trat.tipo_tratamiento, NVL(st.stock, 0), NVL(cadu.cantidad, 0), "
                "NVL(st.stock, 0) - NVL(cadu.cantidad, 0) "
                "ORDER BY MAX(entr.fecha_entrega)")
        cursor.execute(query, [id_receta])
        cursor.rowfactory = fabricaDiccionario(cursor)
        recetaDetalle = cursor.fetchall()  
        permanenteEntregadoAnterior = True
        datos = {
            'recetaDetalle' : recetaDetalle,
            'entregadoAnterior' : permanenteEntregadoAnterior,
            'receta' : receta,
            'tutor' : tutor,
        }
    elif medicPermanente == 0:
        bd = ConexionBD()
        con = bd.conectar()
        cursor = con.cursor()
        query = (
            "SELECT rec.fecha_receta, "
            "detalle.codigo AS CODIGO_MED, "
            "med.nombre_medicamento, "
            "med.descripcion, "
            "tipo_med.nombre_tipo_med AS TIPO_MEDICAMENTO, "
            "detalle.id_receta, "
            "detalle.posologia, "
            "tratamiento.tipo_tratamiento, "
            "(CASE WHEN upper(tratamiento.tipo_tratamiento) = 'PERMANENTE' THEN 1 ELSE 0 END) AS ES_PERMANENTE, "
            "detalle.duracion_tratamiento, "
            "tiempo.nombre_med_tiempo, "
            "pers.rut ||'-'|| pers.dv AS RUT_PACIENTE, "
            "pers.nombres || ' ' || pers.apellido_paterno || ' ' || pers.apellido_materno as NOMBRE_PACIENTE, "
            "NVL(stock.stock, 0) AS STOCK_TOTAL, "
            "NVL(cadu.cantidad, 0) as CADUCADOS, "
            "(CASE WHEN NVL(stock.stock, 0) - NVL(cadu.cantidad, 0) - "
            "NVL((SELECT SUM(reserva.cantidad) FROM reserva_medicamento reserva JOIN receta ON reserva.id_receta = receta.id_receta JOIN persona ON receta.rut_paciente = persona.rut "
            "WHERE persona.id_centro = pers.id_centro AND reserva.codigo = detalle.codigo),0) <= 0 THEN 0 "
            "ELSE NVL(stock.stock, 0) - NVL(cadu.cantidad, 0) - "
            "NVL((SELECT SUM(reserva.cantidad) FROM reserva_medicamento reserva JOIN receta ON reserva.id_receta = receta.id_receta JOIN persona ON receta.rut_paciente = persona.rut  "
            "WHERE persona.id_centro = pers.id_centro AND reserva.codigo = detalle.codigo),0) END) AS STOCK_DISPONIBLE, "
            "NVL((SELECT SUM(reserva.cantidad) FROM reserva_medicamento reserva JOIN receta ON reserva.id_receta = receta.id_receta JOIN persona ON receta.rut_paciente = persona.rut WHERE persona.id_centro = pers.id_centro AND reserva.codigo = detalle.codigo), 0) AS RESERVADOS, "
            "(CASE WHEN (SELECT COUNT(id_reserva) FROM reserva_medicamento "
            "WHERE codigo = detalle.codigo AND id_receta = detalle.id_receta AND entregado = 0) = 0 THEN 0 "
            "ELSE 1 END) AS RESERVADO "
            "FROM detalle_receta detalle INNER JOIN tipo_tratamiento tratamiento ON detalle.id_tipo_tratamiento = tratamiento.id_tipo_tratamiento "
            "INNER JOIN medida_tiempo tiempo ON detalle.id_medida_t = tiempo.id_medida_t "
            "INNER JOIN receta rec ON detalle.id_receta = rec.id_receta "
            "INNER JOIN persona pers ON rec.rut_paciente = pers.rut "
            "INNER JOIN stock_medicamento stock ON detalle.codigo = stock.codigo AND pers.id_centro = stock.id_centro "
            "INNER JOIN caducado cadu ON cadu.codigo = detalle.codigo AND cadu.id_centro = pers.id_centro "
            "INNER JOIN medicamento med ON detalle.codigo = med.codigo "
            "INNER JOIN tipo_medicamento tipo_med ON tipo_med.id_tipo_med = med.id_tipo_med "
            "LEFT JOIN entrega_medicamento entr ON detalle.codigo = entr.codigo AND detalle.id_receta = entr.id_receta "
            "WHERE detalle.id_receta = :id_receta "
            "AND entr.codigo IS NULL AND entr.id_receta IS NULL "
            "ORDER BY detalle.codigo ASC"
        )
        cursor.execute(query, [id_receta])
        cursor.rowfactory = fabricaDiccionario(cursor)
        recetaDetalle = cursor.fetchall()
        permanenteEntregadoAnterior = False
        datos = {
            'recetaDetalle' : recetaDetalle,
            'entregadoAnterior' : permanenteEntregadoAnterior,
            'receta' : receta,
            'tutor' : tutor,
        }
    if request.method == 'POST':
        if 'boton_reserva_1' in request.POST:
            opcForm = 2
            codMed = request.POST['codigo_medicamento_2_1']
            cantidadReserva = int(request.POST['cantidad_reserva_2_1'])
            tipoEntrega = 1
        if 'boton_reserva_2' in request.POST:
            opcForm = 2
            codMed = request.POST['codigo_medicamento_2_2']
            cantidadReserva = int(request.POST['cantidad_reserva_2_2'])
            tipoEntrega = 1
        if 'boton_entrega_1' in request.POST:
            opcForm = 1
            codMed = request.POST['codigo_medicamento_1_1']
            cantidadEntrega = int(request.POST['cantidad_entrega_1_1'])
            tipoEntrega = 1
        if 'boton_entrega_2' in request.POST:
            opcForm = 1
            codMed = request.POST['codigo_medicamento_1_2']
            tipoEntrega = 1
            cantidadEntrega = int(request.POST['cantidad_entrega_1_2'])
        if 'boton_particular' in request.POST:
            opcForm = 3
            codMed = request.POST['codigo_medicamento_particular']
            cantidadEntrega = 0
            tipoEntrega = 2
        if opcForm == 1:
            #cantidadEntrega = request.POST['cantidad_entrega_1']
            bd = ConexionBD()
            con = bd.conectar()
            cursor = con.cursor()
            #existeStock = cursor.var(bool)
            existeStock = cursor.callfunc('pkg_farmacia.fn_stock_suficiente', bool, [codMed, request.user.rut.id_centro.id_centro, cantidadEntrega])
            if existeStock:
                resultado = cursor.var(int)
                cursor.callproc('pkg_farmacia.sp_entregar_medicamento', [cantidadEntrega, codMed, id_receta, request.user.rut.rut, tipoEntrega, resultado])
                if resultado.getvalue() == 1:
                    return redirect('resultado-entrega', id_receta = id_receta, codigo_med=codMed, cantidad=cantidadEntrega, numMensaje=1)
                elif resultado.getvalue() == 2:
                    return redirect('resultado-entrega', id_receta = id_receta, codigo_med=0, cantidad=0, numMensaje=2)
                else:
                    return redirect('resultado-entrega', id_receta = id_receta, codigo_med=0, cantidad=0, numMensaje=0)
        if opcForm == 2:
            bd = ConexionBD()
            con = bd.conectar()
            cursor = con.cursor()
            resultado = cursor.var(int)
            cursor.callproc('pkg_farmacia.sp_crear_reserva_medicamento', [codMed, id_receta, request.user.rut.rut, cantidadReserva, resultado])
            if resultado.getvalue() == 1:
                return redirect('resultado-entrega', id_receta=id_receta, codigo_med=codMed, cantidad=cantidadReserva, numMensaje=3)
            if resultado.getvalue() == 2:
                return redirect('resultado-entrega', id_receta=id_receta, codigo_med=codMed, cantidad=0, numMensaje=4)
            if resultado.getvalue() == 0:
                return redirect('resultado-entrega', id_receta = id_receta, codigo_med=0, cantidad=0, numMensaje=0)
        #Adquisición Particular
        if opcForm == 3:
            bd = ConexionBD()
            con = bd.conectar()
            cursor = con.cursor()
            resultado = cursor.var(int)
            cursor.callproc('pkg_farmacia.sp_entregar_medicamento', [cantidadEntrega, codMed, id_receta, request.user.rut.rut, tipoEntrega, resultado])
            if resultado.getvalue() == 1:
                return redirect('resultado-entrega', id_receta = id_receta, codigo_med=codMed, cantidad=0, numMensaje=6)
    return render(request, 'autofarmapage/farmacia/entrega_medicamento.html', datos)

def entregaResultado(request, id_receta, codigo_med, cantidad, numMensaje):
    datos = {}
    if numMensaje == 1:
        medicamento = Medicamento.objects.get(codigo=codigo_med)
        mensaje = 'La entrega del Medicamento ' + medicamento.nombre_medicamento + ' ha sido registrada.'
        datos = {
            'numero_mensaje' : numMensaje,
            'mensaje' : mensaje,
            'cantidad' : cantidad,
            'medicamento' : medicamento,
            'id_receta' : id_receta,
        }
        return render(request, 'autofarmapage/farmacia/entrega_resultado.html', datos)
    elif numMensaje == 0:
        mensaje = 'Se ha producido un error al procesar los datos, por favor intente nuevamente.'
        datos = {'mensaje' : mensaje, 'numero_mensaje' : numMensaje}
        return render(request, 'autofarmapage/farmacia/entrega_resultado.html', datos)
    elif numMensaje == 2:
        mensaje = 'No hay suficiente Stock disponible en Bodega.'
        datos = {'mensaje' : mensaje, 'numero_mensaje' : numMensaje}
    elif numMensaje == 3:
        medicamento = Medicamento.objects.get(codigo=codigo_med)
        mensaje = 'Reserva del Medicamento ' + medicamento.nombre_medicamento + ' realizada.'
        datos = {
            'numero_mensaje' : numMensaje,
            'mensaje' : mensaje,
            'cantidad' : cantidad,
            'medicamento' : medicamento,
            'id_receta' : id_receta,
        }
    elif numMensaje == 4:
        reserva = ReservaMedicamento.objects.filter(id_receta=id_receta).filter(codigo=codigo_med)
        mensaje = 'Ya existe una reserva registrada en el sistema.'
        datos = {
            'mensaje' : mensaje,
            'reserva' : reserva,
            'numero_mensaje' : numMensaje
        }
    elif numMensaje == 5:
        medicamento = Medicamento.objects.get(codigo=codigo_med)
        mensaje = 'La entrega del Medicamento ' + medicamento.nombre_medicamento + ' ha sido registrada.'
        datos = {
            'numero_mensaje' : numMensaje,
            'mensaje' : mensaje,
            'cantidad' : cantidad,
            'medicamento' : medicamento,
            'id_receta' : id_receta,
        }
    elif numMensaje == 6:
        medicamento = Medicamento.objects.get(codigo=codigo_med)
        mensaje = 'El Medicamento ' + medicamento.nombre_medicamento + ' ha sido marcado para Adquirir Particularmente.'
        datos = {
            'numero_mensaje': numMensaje,
            'mensaje': mensaje,
            'medicamento': medicamento,
            'id_receta': id_receta
        }
    return render(request, 'autofarmapage/farmacia/entrega_resultado.html', datos)

def reservaLista(request):
    if request.method == 'GET':
        criterioSearch = request.GET.get('q')
        if criterioSearch is not None:
            rutSearch = soloCuerpoRut(criterioSearch)
            query = (
                "SELECT reserva.fecha_reserva, "
                "pers.rut, "
                "pers.nombres ||' '|| pers.apellido_paterno ||' '|| pers.apellido_materno as NOMBRE_PACIENTE, "
                "med.nombre_medicamento, "
                "reserva.stock_disponible, "
                "(CASE WHEN reserva.stock_disponible = 1 THEN 'Sí' ELSE 'No' END) AS LISTO_ENTREGAR, "
                "reserva.id_reserva "
                "FROM reserva_medicamento reserva "
                "INNER JOIN receta rec ON reserva.id_receta = rec.id_receta "
                "INNER JOIN persona pers ON rec.rut_paciente = pers.rut "
                "INNER JOIN medicamento med ON reserva.codigo = med.codigo "
                "WHERE entregado = 0 "
                "AND pers.rut = :rutSearch "
                "ORDER BY reserva.fecha_reserva"
            )
    bd = ConexionBD()
    con = bd.conectar()
    cursor = con.cursor()
    query = ("SELECT reserva.fecha_reserva, "
            "pers.rut, "
            "pers.nombres ||' '|| pers.apellido_paterno ||' '|| pers.apellido_materno as NOMBRE_PACIENTE, "
            "med.nombre_medicamento, "
            "reserva.stock_disponible, "
            "(CASE WHEN reserva.stock_disponible = 1 THEN 'Sí' ELSE 'No' END) AS LISTO_ENTREGAR, "
            "reserva.id_reserva "
            "FROM reserva_medicamento reserva "
            "INNER JOIN receta rec ON reserva.id_receta = rec.id_receta "
            "INNER JOIN persona pers ON rec.rut_paciente = pers.rut "
            "INNER JOIN medicamento med ON reserva.codigo = med.codigo "
            "WHERE entregado = 0 "
            "ORDER BY reserva.fecha_reserva"
    )
    cursor.execute(query)
    cursor.rowfactory = fabricaDiccionario(cursor)
    reservas = cursor.fetchall()
    datos = {
        'reservas' : reservas,
    }
    return render(request, 'autofarmapage/farmacia/reservas-lista.html', datos)

def reservaDetalle(request, id_reserva):
    query=(
        "SELECT med.nombre_medicamento, "
        "med.descripcion, "
        "tipo_med.nombre_tipo_med AS TIPO_MEDICAMENTO, "
        "detalle.posologia, "
        "reserva.cantidad, "
        "reserva.id_receta, "
        "reserva.id_reserva, "
        "pers.rut ||'-'||pers.dv AS RUT_PACIENTE, "
        "initcap(pers.nombres) ||' '|| initcap(pers.apellido_paterno)||' '||initcap(pers.apellido_materno) AS NOMBRE_PACIENTE, "
        "reserva.codigo, "
        "reserva.stock_disponible "
        "FROM reserva_medicamento reserva "
        "INNER JOIN detalle_receta detalle ON reserva.id_receta = detalle.id_receta AND reserva.codigo = detalle.codigo "
        "INNER JOIN receta rec ON detalle.id_receta = rec.id_receta "
        "INNER JOIN persona pers ON rec.rut_paciente = pers.rut "
        "INNER JOIN medicamento med ON med.codigo = reserva.codigo "
        "INNER JOIN tipo_medicamento tipo_med ON med.id_tipo_med = tipo_med.id_tipo_med "
        "WHERE reserva.id_reserva = :id_reserva"
    )
    bd = ConexionBD()
    con = bd.conectar()
    cursor = con.cursor()
    cursor.execute(query, [id_reserva])
    cursor.rowfactory = fabricaDiccionario(cursor)
    reserva = cursor.fetchall()
    datos ={
        'reserva' : reserva,
    }
    if request.method == 'POST':
        spIdReserva = int(request.POST['id_reserva'])
        id_receta = reserva[0]['ID_RECETA']
        codigo_med = reserva[0]['CODIGO']
        cantidad = reserva[0]['CANTIDAD']
        bd = ConexionBD()
        con = bd.conectar()
        cursor = con.cursor()
        resultado = cursor.var(int)
        cursor.callproc('pkg_farmacia.sp_entregar_medicamento_reserva', [spIdReserva, request.user.rut.rut, resultado])
        if resultado.getvalue() == 1:
            return redirect('resultado-entrega', id_receta = id_receta, codigo_med=codigo_med, cantidad=cantidad, numMensaje=5)
        else:
            return redirect('resultado-entrega', id_receta = spIdReserva, codigo_med=0, cantidad=0, numMensaje=0)
    return render(request, 'autofarmapage/farmacia/reservas-detalle.html', datos)

#################
# VISTAS MÉDICO #
#################

#Vista del home de Médico
def home_medico(request):
    return render(request, 'autofarmapage/home_medico.html', {})

#Vista de Agregar Paciente (Médico)
def agregarpaciente(request):
    # Querys para poblar los select del formulario de creacion de persona
    #regiones = Region.objects.all()
    regiones = Region.objects.filter(id_region=request.user.rut.id_comuna.id_region.id_region)
    #ciudades = Comuna.objects.all().order_by('nombre_comuna')
    ciudades = Comuna.objects.filter(id_region=request.user.rut.id_comuna.id_region).order_by("nombre_comuna")
    #centro_salud = CentroSalud.objects.all().order_by('id_comuna')
    centro_salud = CentroSalud.objects.filter(id_centro=request.user.rut.id_centro.id_centro)

    if request.method == 'POST':
        rut = request.POST['rut']
        dv = soloDigitoVerificador(rut)
        rut = soloCuerpoRut(rut)
        nombres = request.POST['nombres']
        app_paterno = request.POST['apellido_paterno']
        app_materno = request.POST['apellido_materno']
        telefono = int(request.POST['telefono'])
        email = request.POST['correo_electronico']
        direccion = request.POST['direccion']
        comuna = int(request.POST['id_comuna'])
        centro_s = int(request.POST['id_centro'])
        rut_tutor = None

        # conexión a la bd
        bd = ConexionBD()
        conn = bd.conectar()
        cursor = conn.cursor()
        realizado = cursor.var(int)
        existe_persona = cursor.var(bool)
        cursor.callfunc('pkg_crear_usuario.fn_existe_persona', existe_persona, [rut])
        #Comprueba si el rut ya está registrado en la bd
        if existe_persona:
            messages.error(request, 'El rut ' + rut + '-' + dv + ' ya está registrado en el sistema.')
        else:
            # Llamado al procedimiento almacenado para crear persona (no crea usuario)
            cursor.callproc('pkg_crear_usuario.sp_crear_persona', [
                            rut, dv, nombres, app_paterno, app_materno, telefono, email, direccion, comuna, centro_s, rut_tutor, realizado])

            if int(realizado.getvalue()) == 1:
                # mensaje exito
                messages.success(request, 'Datos agregados al Sistema.')
                # ----------------ACÁ SERIA CREAR PERSONA
                usuario = Usuario.objects.create_user(rut)
                mensaje_email = 'Tu usuario es ' + \
                    rut + ' .Tu contraseña es ' + rut[0:4]

                # envío de mail con el usuario y la contraseña
                send_mail(
                    'Bienvenido a Autofarma.',
                    mensaje_email,
                    'torpedo.page@gmail.com',
                    [email],
                    fail_silently=False
                )
            elif int(realizado.getvalue()) == 0:
                # mesaje error
                messages.error(
                    request, 'Se ha producido un problema y los datos no han sido almacenados. Por Favor intente nuevamente.')
    return render(request, 'autofarmapage/agregar-paciente.html', {'regiones': regiones, 'ciudades': ciudades, 'centro_salud': centro_salud, })

#Crear Receta Paso 1: Guardado en Tabla Receta
def crearreceta(request):
    persona = Persona.objects.all().filter(id_centro=request.user.rut.id_centro)
    rutpat = None
    nombrePaciente = None
    if request.method == 'GET':
        campo_busqueda = request.GET.get("rutpaciente")
        if campo_busqueda is not None:
            rut = request.GET['rutpaciente']
            for i in persona:
                if i.rut == rut:
                    nombrePaciente = i.nombres + " " + i.apellido_paterno + " " + i.apellido_materno
                    rutpat = i.rut + "-" + i.dv
                    messages.success(request, 'Paciente encontrado satisfactoriamente.')
    elif request.method == 'POST':
        rut_medico = request.POST['rutmedico']
        rut_medico = rut_medico.replace('-', '')
        rut_medico = rut_medico[0: len(rut_medico) - 1]
        rutpaciente = request.POST['pacienterut']
        rutpaciente = rutpaciente.replace('-', '')
        rutpaciente = rutpaciente[0: len(rutpaciente) - 1]
        print(rutpaciente)
        print(rut_medico)
        fecha = datetime.now()
        #rut paciente#
        # conexión a la bd
        bd = ConexionBD()
        con = bd.conectar()
        cursor = con.cursor()
        realizado = cursor.var(int)
        retorno = cursor.var(int)
        cursor.callproc('pkg_administrar_receta.sp_nueva_receta', [
                        rut_medico, fecha, rutpaciente, realizado, retorno])
        id_receta = retorno.getvalue()
        if int(realizado.getvalue()) == 1:
            return redirect('crear-receta2', id_receta)
        elif int(realizado.getvalue()) == 0:
            messages.error(request, 'Debe realizar la búsqueda del paciente')
    return render(request, 'autofarmapage/crear-receta.html', {'nombrePaciente': nombrePaciente, 'rutpat': rutpat})

#Crear Receta Paso 2: Guardado en Tabla Detalle_Receta
def crearreceta2(request, id_receta):
    recetapk = Receta.objects.get(id_receta=id_receta)
    medidaTiempo = MedidaTiempo.objects.all()
    tratamiento = TipoTratamiento.objects.all()
    remedios = None
    detallereceta = DetalleReceta.objects.filter(id_receta=id_receta)
    data5 = {
        'recetapk': recetapk,
        'tratamiento': tratamiento,
        'remedios': remedios,
        'detallereceta':detallereceta,
        'medidaTiempo' : medidaTiempo
    }
    if request.method == 'GET':
        campo = request.GET.get('q')
        submitBtn = request.GET.get('submit')
        if campo is not None:
            remedios = Medicamento.objects.filter(
                nombre_medicamento__icontains=campo)
            data5 = {
                'recetapk': recetapk,
                'tratamiento': tratamiento,
                'remedios': remedios,
                'detallereceta':detallereceta,
                'medidaTiempo' : medidaTiempo
            }
            return render(request, 'autofarmapage/crear-receta2.html', data5)
    elif request.method == 'POST':
        posologia = request.POST['posologia']
        duracion = request.POST['duracion']
        dosis = request.POST['dosis']
        tipotratamiento = request.POST['tipo_tratamiento']
        #idreceta = request.POST['idreceta']
        codigo = request.POST['medicamentoadd']
        idMedTiempo = request.POST['medida_tiempo']
        bd = ConexionBD()
        con = bd.conectar()
        cursor = con.cursor()
        realizado = cursor.var(int)
        cursor.callproc('pkg_administrar_receta.sp_ingresar_detalle_receta', [
                        posologia, duracion, dosis, tipotratamiento, id_receta, codigo, idMedTiempo, realizado])
        if realizado.getvalue() == 1:
            messages.success(request, "Medicamento Agregado")
        elif realizado.getvalue() == 0:
            messages.success(request, "Complete todos los campos.")
    return render(request, 'autofarmapage/crear-receta2.html', data5)

# Vista Ver Receta (Visualizar la receta recién prescrita)
def verReceta(request, id_receta):
    receta = Receta.objects.get(id_receta=id_receta)
    detallereceta = DetalleReceta.objects.filter(id_receta=id_receta)
    data = {
        'receta': receta,
        'detallereceta': detallereceta
        }
    return render(request, 'autofarmapage/ver-receta.html', data) 

#Vista Registrar Tutor (Se Registra una nueva Persona y Usuario) (Médico)
def registrartutor(request):
    #regiones = Region.objects.all()
    regiones = Region.objects.filter(id_region=request.user.rut.id_comuna.id_region.id_region)
    #ciudades = Comuna.objects.all().order_by('nombre_comuna')
    ciudades = Comuna.objects.filter(id_region=request.user.rut.id_comuna.id_region).order_by("nombre_comuna")
    #centro_salud = CentroSalud.objects.all().order_by('id_comuna')
    centro_salud = CentroSalud.objects.filter(id_centro=request.user.rut.id_centro.id_centro)

    if request.method == 'POST':
        rut = request.POST['rut']
        dv = soloDigitoVerificador(rut)
        rut = soloCuerpoRut(rut)
        nombres = request.POST['nombres']
        app_paterno = request.POST['apellido_paterno']
        app_materno = request.POST['apellido_materno']
        telefono = int(request.POST['telefono'])
        email = request.POST['correo_electronico']
        direccion = request.POST['direccion']
        comuna = int(request.POST['id_comuna'])
        centro_s = int(request.POST['id_centro'])
        rut_tutor = None

        # conexión a la bd
        bd = ConexionBD()
        conn = bd.conectar()
        cursor = conn.cursor()
        realizado = cursor.var(int)
        existe_persona = cursor.var(bool)
        if existe_persona:
            messages.error(request, 'El rut ' + rut + '-' + dv + ' ya está registrado en el sistema.')
        else:
            # Llamado al procedimiento almacenado para crear persona (no crea usuario)
            cursor.callproc('pkg_crear_usuario.sp_crear_persona', [
                            rut, dv, nombres, app_paterno, app_materno, telefono, email, direccion, comuna, centro_s, rut_tutor, realizado])

            if int(realizado.getvalue()) == 1:
                # mensaje exito
                messages.success(request, 'Datos agregados al Sistema.')
                # ----------------ACÁ SERIA CREAR PERSONA
                usuario = Usuario.objects.create_user(rut)
                mensaje_email = 'Tu usuario es ' + \
                    rut + ' .Tu contraseña es ' + rut[0:4]

                # envío de mail con el usuario y la contraseña
                send_mail(
                    'Bienvenido a Autofarma.',
                    mensaje_email,
                    'torpedo.page@gmail.com',
                    [email],
                    fail_silently=False
                )
            elif int(realizado.getvalue()) == 0:
                # mesaje error
                messages.error(
                    request, 'Se ha producido un problema y los datos no han sido almacenados. Por Favor intente nuevamente.')
    return render(request, 'autofarmapage/registrar-tutor.html', {'regiones': regiones, 'ciudades': ciudades, 'centro_salud': centro_salud, })

#Vista Agregar Tutor (Se agregar el RUT del Tutor a una Persona)
def agregarTutor(request, rut):
    paciente = Persona.objects.get(rut=rut[0: len(rut) - 2])
    ruttutor = None
    nombreTutor = None
    if request.method == 'GET':
        campoBuscar = request.GET.get("ruttutor")
        if campoBuscar is not None:
            persona = Persona.objects.all()
            for i in persona:
                if i.rut == campoBuscar:
                    ruttutor = i.rut + '-' + i.dv
                    nombreTutor = i.nombres + ' ' +i.apellido_paterno + ' ' +i.apellido_materno
                    messages.success(request, 'Tutor encontrado en el sistema.')
    elif request.method == 'POST':
        rutdeltutor = request.POST['rutu']
        rutdeltutor = rutdeltutor.replace('-', '')
        rutdeltutor = rutdeltutor[0: len(rutdeltutor) - 2]
        print(rutdeltutor)
        # conexión a la bd
        bd = ConexionBD()
        con = bd.conectar()
        cursor = con.cursor()
        realizado = cursor.var(int)
        cursor.callproc('pkg_crear_usuario.sp_crear_tutor', [rutdeltutor, paciente.rut, realizado])
        print(realizado.getvalue())
        if realizado.getvalue() == 1:
            return redirect('crear-receta')
        elif realizado.getvalue() == 0:
            messages.error(
                request, 'Ocurrió un error :( - Intente ingresando un rut en el buscador')
    return render(request, 'autofarmapage/agregar-tutor.html', {'paciente': paciente, 'ruttutor': ruttutor, 'nombreTutor': nombreTutor})

#Vista Listar Recetas (Médico)
def verRecetas(request):
    receta = Receta.objects.all().order_by('fecha_receta')
    data = {
        'receta':receta,
    }
    if request.method == 'GET':
        entrada = request.GET.get('q')
        btn = request.GET.get('submit')
        if entrada is not None:
            receta = Receta.objects.filter(rut_paciente=entrada)
            data={
                'receta':receta.order_by('-fecha_receta'),
            }
            return render(request, 'autofarmapage/ver-recetas.html', data)   
    return render(request, 'autofarmapage/ver-recetas.html', data) 

#Vista del Detalle de la Receta (Al seleccionar una de la lista de recetas)
def verReceta2(request, id_receta):
    receta = Receta.objects.get(id_receta=id_receta)
    detallereceta = DetalleReceta.objects.filter(id_receta=id_receta)
    data = {
        'receta':receta, 
        'detallereceta':detallereceta
    }
    return render(request, 'autofarmapage/ver-receta2.html', data)

#rest_framework
class RecetaViewSet(viewsets.ModelViewSet):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer    

class ApiRecetaListView(generics.ListAPIView):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer
    pagination_class = PageNumberPagination
    filter_backends = (SearchFilter, OrderingFilter)
    pagination_class = PageNumberPagination
    search_fields = ('id_receta', 'rut_paciente__rut')

class ApiUsuario(generics.ListAPIView):
    queryset = Persona.objects.all()
    serializer_class =  PersonaSerializer
    pagination_class = PageNumberPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('rut',)

def listaReservasMovil(request, rut_paciente):
    if request.method == 'GET':
        query = (
            "SELECT reserva.id_reserva AS ID_RESERVA, "
            "reserva.codigo AS CODIGO, "
            "med.nombre_medicamento AS NOMBRE_MEDICAMENTO, "
            "reserva.cantidad AS CANTIDAD, "
            "reserva.stock_disponible AS DISPONIBLE_ENTREGA, "
            "reserva.id_receta AS ID_RECETA, "
            "reserva.fecha_reserva AS FECHA_RESERVA "
            "FROM reserva_medicamento reserva "
            "INNER JOIN detalle_receta detalle ON reserva.id_receta = detalle.id_receta AND reserva.codigo = detalle.codigo "
            "INNER JOIN medicamento med ON detalle.codigo = med.codigo "
            "INNER JOIN receta ON detalle.id_receta = receta.id_receta "
            "INNER JOIN persona ON receta.rut_paciente = persona.rut "
            "WHERE entregado = 0 AND persona.rut = :rut_paciente"
        )
        bd = ConexionBD()
        con = bd.conectar()
        cursor = con.cursor()
        cursor.execute(query, [rut_paciente])
        cursor.rowfactory = fabricaDiccionario(cursor)
        reserva = cursor.fetchall()
        serializer = ReservaSerializer(reserva,many=True)
        return JsonResponse(serializer.data, safe=False)

"""class ResetPasswordRequestView(FormView):
    template_name = "registration/password_reset_formu.html"
    success_url = "/"
    form_class = PasswordResetRequestForm

    def form_valid(self, form):
        form = super().form_valid(form)
        data = form.cleaned_data["rut_usuario"]
        user = Usuario.objects.filter(rut=data).first()
        if user:
            c = {
                'email' : user.rut.correo_electronico,
                'domain' : self.request.META['HTTP_HOST'],
                'site_name' : 'Autofarma',
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'user' : user,
                'token' : default_token_generator.make_token(user),
                'protocol' : self.request.scheme,
            }
            email_template_name='registration/password_reset_email.html'
            subject="Reseteo Contraseña"
            email=loader.render_to_string(email_template_name, c)
            send_mail(subject, email, "torpedo.page@gmail.com", [user.rut.correo_electronico], fail_silently=False)
        return form

        form.send_email()
        return super().form_valid(form)"""

##################
#RESET CONTRASEÑA#
##################

def resetPasswordRut(request):
    if request.method == 'POST':
        rut = soloCuerpoRut(request.POST['rut'])
        usuario = Usuario.objects.filter(rut=rut).first()
        if usuario is not None:
            password = Usuario.objects.make_random_password(length=11)
            print(password)
            usuario.set_password(password)
            usuario.save()
            mensaje_mail = ('Se ha restablecido la contraseña para el usuario rut ' +
                            request.POST['rut'] + ". "
                            "Tu nueva contraseña es " + password
            )
            send_mail(
                'Autofarma, Reset Contraseña.',
                mensaje_mail,
                'torpedo.page@gmail.com',
                [usuario.email],
                fail_silently=False,
                html = ''
            )
            return render(request, 'registration/password_reset_success.html', {})
        else:
            alerta = (
                "El usuario " + request.POST['rut'] + " no se encuentra registrado en "
                "nuestra base de datos. Por favor verifique los datos y vuelva a intentarlo."
            )
            return render(request, 'registration/password_reset_run.html', {'alerta': alerta})
    return render(request, 'registration/password_reset_run.html', {})

def resetPasswordRutSuccess(request):
    return render(request, 'registration/password_reset_success.html', {})

#####################
#VISTA INFORME STOCK#
#####################

def render_informestock_html(request):
    centroSalud = request.user.rut.id_centro.id_centro
    dataInforme = listar_informe_stock(centroSalud)
    return render(request, 'autofarmapage/formatoInforme.html', dataInforme)     

# VISTA PDF INFORME STOCK
def renderizar_pdf(template_src, datos_informe={}):
    template = get_template(template_src)
    html = template.render(datos_informe)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='aplication/pdf')
    return None

class MostrarPDFSTOCK(View):
    def get(self, request, nombre_medicamento):
        conexion = ConexionBD()
        centroSalud = request.user.rut.id_centro.id_centro
        data1 = stock_informe(centroSalud, nombre_medicamento, conexion)
        now = datetime.now()
        data = { 'now': now,
                 'data1':data1, }
        pdf = renderizar_pdf('autofarmapage/formatoInforme.html', data)
        return HttpResponse(pdf, content_type='application/pdf')

class DescargarPDF(View):
    def get(self, request, nombre_medicamento):
        conexion = ConexionBD()
        centroSalud = request.user.rut.id_centro.id_centro
        data1 = stock_informe(centroSalud, nombre_medicamento, conexion)
        now = datetime.now()
        data = { 'now': now,
                 'data1':data1, }
        pdf = renderizar_pdf('autofarmapage/formatoInforme.html', data)
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Informe_stock_%s.pdf" %("centro_N-" + str(centroSalud))
        content = "attachment; filename='%s'" %(filename)
        response['Content-Disposition'] = content
        return response

def listar_informe_stock(id_centro):
    bd = ConexionBD()
    con = bd.conectar()
    cursor = con.cursor()
    cursor.prepare("""SELECT me.nombre_medicamento,  
                      me.fabricante, tm.nombre_tipo_med, 
                      st.stock, ca.cantidad AS CANT_CADUCADOS, 
                      st.stock - ca.cantidad AS TOTAL_DISPONIBLE, 
                      (SELECT nombre_centro FROM centro_salud WHERE id_centro=st.id_centro) AS CENTRO_SALUD, 
                      (SELECT co.nombre_comuna FROM comuna co JOIN centro_salud cs ON cs.id_comuna=co.id_comuna WHERE id_centro = st.id_centro) AS COMUNA 
                      FROM stock_medicamento st JOIN medicamento me ON st.codigo = me.codigo 
                      JOIN caducado ca ON ca.codigo = me.codigo 
                      JOIN tipo_medicamento tm ON tm.id_tipo_med = me.id_tipo_med 
                      WHERE st.id_centro = :id_centro""")
    cursor.execute(None, id_centro = id_centro)   
    #cursor.execute(query, id_centro=301)
    cursor.rowfactory = fabricaDiccionario(cursor)
    informe_stock = cursor.fetchall()
    datos ={
            'informe_stock': informe_stock,
        }             
    return datos

def stock_informe(id_centro, nombre_medicamento, conexion):
    con = conexion.conectar()
    cursor = con.cursor()
    cursor.prepare("SELECT me.nombre_medicamento,  me.fabricante, tm.nombre_tipo_med, st.stock, ca.cantidad AS CANT_CADUCADOS, st.stock - ca.cantidad AS TOTAL_DISPONIBLE, (SELECT nombre_centro FROM centro_salud WHERE id_centro=st.id_centro) AS CENTRO_SALUD, (SELECT co.nombre_comuna FROM comuna co JOIN centro_salud cs ON cs.id_comuna=co.id_comuna WHERE id_centro = st.id_centro) AS COMUNA FROM stock_medicamento st JOIN medicamento me ON st.codigo = me.codigo JOIN caducado ca ON ca.codigo = me.codigo JOIN tipo_medicamento tm ON tm.id_tipo_med = me.id_tipo_med WHERE st.id_centro = :id_centro AND me.nombre_medicamento = :nombre_medicamento")
    cursor.execute(None, id_centro = id_centro, nombre_medicamento = nombre_medicamento)
    cursor.rowfactory = fabricaDiccionario(cursor)
    informe_stock = cursor.fetchall()
    datos ={
            'informe_stock': informe_stock,
        }
    return datos

#Vista de la Lista de Informes
def listarinforme(request):
    #Obtiene todos los informes
    """informe = RegistroInformes.objects.all()
    datainfo = {
        'informe': informe
    }"""
    centroSalud = request.user.rut.id_centro.id_centro
    dataInforme = listar_informe_stock(centroSalud)
    return render(request, 'autofarmapage/listar-informe.html', dataInforme)    
