# Inhoudelijke geografische controles

De JSON-bestanden bevatten beslissingen over de koppeling tussen een lokale
OV-versinhoud en een geografische bronentiteit. Een bevestigde koppeling bewijst
niet dat de moderne coördinaat zeker is. Die zekerheid blijft afzonderlijk staan.

- `confirmed`: onderbouwde tekstkoppeling; publiceer als `agent-reviewed`.
- `rejected`: deze verskoppeling niet publiceren; de beslissing blijft bewaard.
- `needs-human-review`: de identificatie blijft onzeker.
- `textSha256`: SHA-256 van de volledige UTF-8-waarde van `text2026`, inclusief
  eventuele markup. Een gewijzigde versinhoud vereist een nieuwe controle.
- `mentionType`: `explicit` voor een plaatsnaam, `origin` voor herkomst en
  `contextual` voor een indirecte verwijzing. Herkomst en context zijn geen
  bewijs dat de beschreven gebeurtenis op die plaats plaatsvond.
- `entities`: aanvullende punten met een afzonderlijke, controleerbare bron.
- `unresolvedCandidates`: nog niet geïdentificeerde namen, zonder verzonnen punt.

`humanReviewed` blijft `false`: deze controles zijn niet als menselijke revisie
gepresenteerd. Tegenstrijdige beslissingen mogen niet stil worden overschreven.
