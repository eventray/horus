<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
  </head>
  <body>
    <a href="${request.route_url('index')}">Back to Index</a>
    % for type in ['success', 'error', 'warning', 'info']:
      % if request.session.peek_flash(type):
        % for message in request.session.pop_flash(type):
          <div class="alert-message ${type}">
            <p><strong>${message}</strong></p>
          </div>
        % endfor
      % endif
    % endfor
    ${request.wrapped_body.decode(request.wrapped_response.charset)|n}
  </body>
</html>
