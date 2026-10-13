from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Correo de trabajo",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "nombre@empresa.com",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Ingrese su contraseña",
            }
        ),
    )
