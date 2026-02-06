from AMAflex.AMAapp import RegistrationForm
from flask import render_template
from AMAflex import app
import config
from configStore import load_config, save_config, missing_required_fields


app.config['SECRET_KEY'] = 'tryout1'
def _base_context():
    cfg = load_config()
    missing = missing_required_fields(cfg)
    ready = len(missing) == 0
    return {
        "config_values": cfg,
        "config_ready": ready,
        "missing_fields": missing,
        "selected_mode": "snapshot",
    }

@app.route("/")
@app.route("/home", methods=['GET', 'POST'])
def home():
    form = RegistrationForm()
    if form.validate_on_submit():
        
        save_config(form)
        ctx = _base_context()
        ctx["setup_message"] = "Configuration saved."
        return render_template('SettingForm.html', title = 'setting', form = form, **ctx)
    return render_template('SettingForm.html', title = 'setting', form = form)
    