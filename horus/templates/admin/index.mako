<%inherit file="horus:templates/layout.mako"/>

<a href="${request.route_url('horus_admin_users_create')}">Create New User</a>

<ul>
  <li><a href="${request.route_url('horus_admin_users_index')}">User List</a></li>
</ul>
