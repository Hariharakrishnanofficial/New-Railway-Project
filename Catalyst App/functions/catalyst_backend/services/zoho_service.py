"""
CloudScale Service — Database integration.
Uses Catalyst SDK for CloudScale database operations.
"""
from repositories.cloudscale_repository import CloudScaleRepository, cloudscale_repo

# Primary export - CloudScale repository singleton
cloudscale = cloudscale_repo

# Backward compatibility alias (for existing code that imports 'zoho')
zoho = cloudscale_repo
