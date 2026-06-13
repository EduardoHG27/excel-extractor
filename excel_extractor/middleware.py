# excel_extractor/middleware.py

class HideServerHeaderMiddleware:
    """
    Middleware para ocultar el header 'Server' por razones de seguridad.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Elimina el header Server que podría mostrar información del servidor
        if 'Server' in response:
            del response['Server']
        return response