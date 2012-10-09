<%inherit file="horus:templates/layout.mako"/>

% for user in users:
  ${user.user_name} [<a href="${request.route_url('horus_admin_users_edit', user_pk=user.pk)}">Edit</a>]
% endfor
