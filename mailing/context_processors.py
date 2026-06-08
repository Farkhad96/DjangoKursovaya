from .permissions import is_manager


def manager_flag(request):
    return {"is_manager": is_manager(request.user)}
