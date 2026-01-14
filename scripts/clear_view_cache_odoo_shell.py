# Run this in Odoo shell to clear view cache
# This will force Odoo to rebuild all views

# Clear view cache
env.registry.clear_cache()
print("✓ Cleared registry cache")

# Invalidate view cache specifically
env['ir.ui.view']._clear_cache()
print("✓ Cleared view cache")

# Also invalidate the specific view if we know it
try:
    # Clear all project.project form views
    env['ir.ui.view'].invalidate_model(['arch_db'])
    print("✓ Invalidated view architecture cache")
except Exception as e:
    print(f"Note: {e}")

env.cr.commit()
print("\n✓ Cache cleared! Restart your Odoo server and refresh your browser.")
