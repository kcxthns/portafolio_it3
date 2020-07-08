from django.urls import path, reverse_lazy, include
from . import views
from django.contrib.auth import views as auth_views
from .views import RecetaViewSet, ApiRecetaListView, ApiUsuario
from rest_framework import routers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import obtain_auth_token

router = routers.DefaultRouter()
router.register('receta', RecetaViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('homeadmi', views.homeadmi, name='homeadmi'),
    path('agregar-usuario', views.agregarusuario, name="agregar-usuario"),
    path('listar-usuario', views.listarusuario, name='listar-usuario'),
    path('listar-informe', views.listarinforme, name='listar-informe'),
    path('editarPersona/<slug:rut>', views.editarPersona, name='editarPersona'),
    path('deshabilitarpage/<slug:rut>', views.deshabilitarUsuario,  name='deshabilitarpage'),
    path('exito-crear-usuario', views.guardadoUsuarioExito, name='exito-crear-usuario'),
    path('exito-guardar-tutor', views.guardadoTutorExito, name='exito-guardar-tutor'),
    path('exito-modificar-usuario', views.modificarUsuarioExito, name='exito-modificar-usuario'),
    path('logout', views.logout),
    path('cambio-centro-salud', views.cambiarCentroSalud, name='cambio-centro-salud'),

    #urls farmacia
    path('inicio-farmacia', views.inicioFarmacia, name='inicio-farmacia'),
    path('homefarma', views.homeFarmacia, name='homefarma'),
    path('agregar-medicamento', views.agregarMedicamento, name='agregar-medicamento'),
    path('agregar-componente', views.agregarComponente, name='agregar-componente'),
    path('listar-medicamento', views.listarMedicamento, name='listar-medicamento'),
    path('exito-crear-medicamento', views.guardadoMedicamentoExito, name='exito-crear-medicamento'),
    path('inicio-entregas', views.inicioEntregas, name='inicio-entregas'),
    path('entregas-pendientes', views.entregasPendientes, name='entregas-pendientes'),
    path('entrega-medicamento/<int:id_receta>', views.entregaMedicamento, name='entrega-medicamento'),
    path('resultado-entrega/<int:id_receta>/<int:codigo_med>/<int:cantidad>/<int:numMensaje>', views.entregaResultado, name='resultado-entrega'),
    path('reservas-lista', views.reservaLista, name='reservas-lista'),
    path('reservas-detalle/<int:id_reserva>', views.reservaDetalle, name='reservas-detalle'),
    path('editar-medicamento/<int:codigoMed>', views.editarMedicamento, name='editar-medicamento'),

    # urls médico
    path('home_medico', views.home_medico, name='home_medico'),
    path('crear-receta', views.crearreceta, name="crear-receta"),
    path('crear-receta2/<int:id_receta>', views.crearreceta2, name="crear-receta2"),
    path('agregar-paciente', views.agregarpaciente, name="agregar-paciente"),
    path('registrar-tutor', views.registrartutor, name="registrar-tutor"),
    path('agregar-tutor/<slug:rut>', views.agregarTutor, name='agregar-tutor'),
    path('ver-recetas', views.verRecetas, name="ver-recetas"),
    path('ver-receta2/<int:id_receta>', views.verReceta2, name='ver-receta2'),

    ###urls del k-prueba
    path('ver-receta/<int:id_receta>', views.verReceta, name='ver-receta'),
    path('ver-receta-movil/<int:id_receta>', views.verRecetaMovil, name='ver-receta-movil'),
    #urls modificaciones contraseña
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_d.html'),
        name='password_change_done'
    ),

    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html'),
        name='password_change'),

     path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done_custom.html'), 
        name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm_custom.html',
        success_url=reverse_lazy('reset_completo')), 
        name='password_reset_confirm'),

    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_formu.html'
    ),
        name='password_reset'),

    path('cambio_exitoso', views.passwordResetCompleto, name='reset_completo'),

    path('reset_password', views.resetPasswordRut, name='reset_pass'),

    path('reset_success', views.resetPasswordRutSuccess, name='reset_success'),

    #rest_framework
    path('api/', include(router.urls)),
    path('api-token-auth/', obtain_auth_token, name='api-token-auth'),
    path('ListReceta', ApiRecetaListView.as_view(), name='ListReceta'),
    path('GetPersona', ApiUsuario.as_view(), name='GetPersona'),
    path('reservas/<int:rut_paciente>', views.listaReservasMovil),

    #generador pdf
    path('pdf_stock/<int:id_informe>', views.MostrarPDFSTOCK.as_view(), name='pdf_stock'),
    path('pdf_download/<int:id_informe>', views.DescargarPDF.as_view(), name='pdf_download'),

    #generador pdf reserva
    path('pdf_reserva/<int:id_informe>', views.MostrarPDFRESERVA.as_view(), name='pdf_reserva'),
    path('pdf_descargar/<int:id_informe>', views.DescargarPDFRESERVA.as_view(), name='pdf_descargar'),
    #url informe stock
    path('informeStock', views.render_informestock_html, name='informeStock'),
    path('informeReserva', views.render_informereserva_html, name='informeReserva'),
    
]