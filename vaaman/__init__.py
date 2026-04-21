__version__ = "0.0.1"






def apply_overrides():
    
    try:
        from vaaman.vaaman.rfq_override import patch_rfq

        
        patch_rfq()
    except Exception:
        pass


apply_overrides()