"""
Blueprint registration — single place to wire every module into the Flask app.
"""

def register_blueprints(app):
    from routes.auth        import auth_bp;        app.register_blueprint(auth_bp)
    from routes.auth_crud   import auth_crud_bp;   app.register_blueprint(auth_crud_bp)
    from routes.bookings    import bookings_bp;    app.register_blueprint(bookings_bp)
    from routes.stations    import stations_bp;    app.register_blueprint(stations_bp)
    from routes.trains      import trains_bp;      app.register_blueprint(trains_bp)
    # from routes.users       import users_bp;       app.register_blueprint(users_bp)  # OLD Zoho version
    from routes.users_cloudscale import users_cloudscale_bp; app.register_blueprint(users_cloudscale_bp)  # NEW CloudScale version
    from routes.train_routes import train_routes_bp; app.register_blueprint(train_routes_bp)
    from routes.coaches     import coaches_bp;     app.register_blueprint(coaches_bp)
    from routes.inventory   import inventory_bp;   app.register_blueprint(inventory_bp)
    from routes.quotas      import quotas_bp;      app.register_blueprint(quotas_bp)
    from routes.overview    import overview_bp;    app.register_blueprint(overview_bp)
    from routes.fares       import fares_bp;       app.register_blueprint(fares_bp)
    from routes.settings    import settings_bp;    app.register_blueprint(settings_bp)
    from routes.announcements import announcements_bp; app.register_blueprint(announcements_bp)
    from routes.ai_routes   import ai_bp;          app.register_blueprint(ai_bp)
    from routes.admin_logs  import admin_logs_bp;  app.register_blueprint(admin_logs_bp)
    from routes.coach_layouts import coach_layouts_bp; app.register_blueprint(coach_layouts_bp)
    # admin_reports registered in app.py with explicit url_prefix
