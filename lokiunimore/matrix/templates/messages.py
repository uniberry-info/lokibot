# ==================================== #

WELCOME_MESSAGE_TEXT = """
Benvenuto allo spazio Matrix dell'Unimore!

Sono {username_text}, il bot buttafuori che verifica le credenziali degli utenti che entrano e permette loro di accedere alle rispettive aree.

Se sei uno studente, puoi ottenere accesso all'Area Studenti verificando la tua identità:
{base_url}/matrix/{token}
"""

# language=html
WELCOME_MESSAGE_HTML = """
<p>
    Benvenuto allo spazio Matrix dell'Unimore!
</p>
<p>
    Sono {username_html}, il bot buttafuori che verifica le credenziali degli utenti che entrano e permette loro di accedere alle rispettive aree.
</p>
<p>
    Se sei uno studente, puoi ottenere accesso all'Area Studenti <a href="{base_url}/matrix/{token}">verificando la tua identità</a>!
</p>
"""

# ==================================== #

SUCCESS_MESSAGE_TEXT = """
Ti sei unito all'Area Studenti: benvenuto!

Se in qualsiasi momento vuoi modificare o eliminare i tuoi dati salvati sul mio database, puoi accedervi dal tuo profilo privato:
{base_url}/matrix/{token}
"""

# language=html
SUCCESS_MESSAGE_HTML = """
<p>
    Ti sei unito all'Area Studenti: benvenuto!
</p>
<p>
    Se in qualsiasi momento vuoi modificare o eliminare i tuoi dati salvati sul mio database, puoi <a href="{base_url}/matrix/{token}">accedervi dal tuo profilo privato</a>!
</p>
"""

# ==================================== #

GOODBYE_MESSAGE_TEXT = """
Hai abbandonato lo spazio Matrix dell'Unimore, quindi ho cancellato i tuoi dati dal mio database; a breve verrai inoltre rimosso da tutte le stanze dello spazio.

Se cambierai idea in futuro, potrai sempre rientrare allo stesso indirizzo!

Abbi un buon proseguimento di giornata! :)
"""

# language=html
GOODBYE_MESSAGE_HTML = """
<p>
    Hai abbandonato lo spazio Matrix dell'Unimore, quindi ho cancellato i tuoi dati dal mio database; a breve verrai inoltre rimosso da tutte le stanze dello spazio.
</p>
<p>
    Se cambierai idea in futuro, potrai sempre rientrare allo stesso indirizzo!
</p>
<p>
    Abbi un buon proseguimento di giornata! :)
</p>
"""

# ==================================== #

UNLINK_MESSAGE_TEXT = """
Hai abbandonato l'Area Studenti dello spazio Unimore, quindi ho scollegato il tuo account Studenti@Unimore dal tuo account Matrix.

Se cambierai idea in futuro, potrai sempre essere riaggiunto all'Area Studenti ricollegando il tuo account:
{base_url}/matrix/{token}

Abbi un buon proseguimento di giornata! :)
"""

# language=html
UNLINK_MESSAGE_HTML = """
<p>
    Hai abbandonato l'Area Studenti dello spazio Unimore, quindi ho scollegato il tuo account Studenti@Unimore dal tuo account Matrix.
</p>
<p>
    Se cambierai idea in futuro, potrai sempre essere riaggiunto all'Area Studenti <a href="{base_url}/matrix/{token}">ricollegando il tuo account</a>!
</p>
<p>
    Abbi un buon proseguimento di giornata! :)
</p>
"""

# ==================================== #

__all__ = (
    "WELCOME_MESSAGE_TEXT",
    "WELCOME_MESSAGE_HTML",
    "SUCCESS_MESSAGE_TEXT",
    "SUCCESS_MESSAGE_HTML",
    "GOODBYE_MESSAGE_TEXT",
    "GOODBYE_MESSAGE_HTML",
    "UNLINK_MESSAGE_TEXT",
    "UNLINK_MESSAGE_HTML",
)
