<%inherit file="horus:templates/layout.mako"/>

<a href="${request.route_url('admin')}">Back to Admin</a>
${render_flash_messages()|n}
<h1>Create User</h1>
${form|n}
