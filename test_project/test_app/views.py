from importd import d
from django.contrib.auth.models import User


@d(r'/', name='list_users')
def list_users(request):
    context = {'users': User.objects.all(), 'usermodel': User}
    return d.render_to_response('list_users.html', context,
                                context_instance=d.RequestContext(request))



@d(r'/<int:user_id>/', name="show_user")
def show_user(request, user_id):
    context = {'user': d.get_object_or_404(User, pk=user_id),
               'usermodel': User}
    return d.render_to_response('show_user.html', context,
                                context_instance=d.RequestContext(request))
