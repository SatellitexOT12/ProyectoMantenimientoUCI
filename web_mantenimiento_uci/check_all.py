import urllib.request

# Test main page (portada) - needs ?as=dev_admin
try:
    r = urllib.request.urlopen('http://127.0.0.1:8801/main/?as=dev_admin')
    html = r.read().decode()
    print('=== MAIN (portada) ===')
    print('Status:', r.status)
    print('sg-sheet:', 'sg-sheet' in html)
    print('sg-page-head:', 'sg-page-head' in html)
    print('sg-btn:', 'sg-btn' in html)
    print('pt-layout:', 'pt-layout' in html)  # portada specific classes
    print('Inicio h1:', '<h1' in html and 'Inicio' in html)
except Exception as e:
    print('Main error:', e)

print()

# Test incidencias list
try:
    r = urllib.request.urlopen('http://127.0.0.1:8801/incidencias/?as=dev_admin')
    html = r.read().decode()
    print('=== INCIDENCIAS ===')
    print('Status:', r.status)
    print('sg-table:', 'sg-table' in html)
    print('sg-btn:', 'sg-btn' in html)
    print('Incidencias title:', 'Incidencias' in html)
    print('sg-col-n:', 'sg-col-n' in html)
except Exception as e:
    print('Incidencias error:', e)

print()

# Test reportar incidencia page (login required)
try:
    r = urllib.request.urlopen('http://127.0.0.1:8801/reportar_incidencia?as=dev_admin')
    html = r.read().decode()
    print('=== REPORTAR ===')
    print('Status:', r.status)
    print('sg-sheet:', 'sg-sheet' in html)
    print('sg-field:', 'sg-field' in html)
    print('sg-btn-primary:', 'sg-btn--primary' in html)
    print('Rep-form:', 'rep-form' in html)
except Exception as e:
    print('Reportar error:', e)

print()

# Test login page (no session)
try:
    r = urllib.request.urlopen('http://127.0.0.1:8801/')
    html = r.read().decode()
    print('=== LOGIN ===')
    print('Status:', r.status)
    print('sg-login:', 'sg-login' in html)
    print('sg-sheet:', 'sg-sheet' in html)
    print('sg-field:', 'sg-field' in html)
    print('sg-foot:', 'sg-foot' in html)
    print('NO lg-frame:', 'lg-frame' not in html)
    print('lang=es:', 'lang="es"' in html)
except Exception as e:
    print('Login error:', e)
