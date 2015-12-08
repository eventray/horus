<%inherit file="horus:templates/layout.mako"/>

<table>
  <tr>
    <th>Username</th>
    <th>Email</th>
    <th>Registered</th>
    <th>Action(s)</th>
  </tr>
% for user in users:
  <tr>
    <td>${user.username}</td>
    <td>${user.email}</td>
    <td>${user.registered_date}</td>
    <td>
      <a href="${request.route_url('admin_users_edit', user_id=user.id)}">Edit</a>
      |
      % if not user.activation:
        <a href="${request.route_url('admin_users_deactivate', user_id=user.id)}">Deactivate</a>
      % endif
      % if not user.is_activated:
        <a href="${request.route_url('admin_users_activate', user_id=user.id)}">Activate</a>
      % endif
    </td>
  </tr>
% endfor
</table>
