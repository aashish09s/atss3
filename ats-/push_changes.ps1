$env:GIT_PAGER = ''
$env:GIT_CONFIG_PARAMETERS = 'core.pager='
git config core.pager ''
git add -A
git commit -m "Add new panels and features - superadmin routes, updated routes and models, frontend components"
git push origin main

