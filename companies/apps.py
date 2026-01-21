from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    name = 'companies'





# # companies/apps.py
# from django.apps import AppConfig

# class CompaniesConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'companies'
    
#     def ready(self):
#         # Import tasks
#         from . import tasks
        
#         # Only run in main process, not in reloads
#         import os
#         if os.environ.get('RUN_MAIN') or os.environ.get('WERKZEUG_RUN_MAIN'):
#             # Setup scheduled tasks
#             tasks.setup_daily_tasks()