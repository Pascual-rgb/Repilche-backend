import re
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

ALIAS_BANCARIO_REGEX = re.compile(r"^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*$")
ALIAS_BANCARIO_ERROR_MESSAGE = (
    "El alias bancario debe tener entre 6 y 20 caracteres alfanuméricos "
    "y puede contener puntos, sin espacios."
)


def validar_alias_bancario(value: str) -> str:
    """
    Validador estándar para alias bancarios (CBU/CVU/Mercado Pago):
    - Alfanumérico con puntos permitidos.
    - No debe comenzar ni terminar con punto, ni tener puntos consecutivos.
    - Sin espacios ni caracteres especiales.
    - Longitud entre 6 y 20 caracteres (tolerando hasta 30 si el campo lo admite).
    - Normaliza el alias convirtiéndolo automáticamente a minúsculas (alias.strip().lower()).
    """
    if value is None or not isinstance(value, str):
        raise ValidationError(ALIAS_BANCARIO_ERROR_MESSAGE)

    alias_clean = value.strip().lower()

    if not alias_clean:
        raise ValidationError(ALIAS_BANCARIO_ERROR_MESSAGE)

    if " " in alias_clean:
        raise ValidationError(ALIAS_BANCARIO_ERROR_MESSAGE)

    # Permitir longitud entre 6 y 20 caracteres (tolerando hasta 30)
    if not (6 <= len(alias_clean) <= 30):
        raise ValidationError(ALIAS_BANCARIO_ERROR_MESSAGE)

    if not ALIAS_BANCARIO_REGEX.match(alias_clean):
        raise ValidationError(ALIAS_BANCARIO_ERROR_MESSAGE)

    return alias_clean


class AliasBancarioValidator:
    """Validador invocable para su uso en campos de serializers o modelos."""

    message = ALIAS_BANCARIO_ERROR_MESSAGE

    def __call__(self, value):
        return validar_alias_bancario(value)

