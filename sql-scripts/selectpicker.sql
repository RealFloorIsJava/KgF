DELIMITER //

/**
 * Selects the next picker in the given match
 */
DROP PROCEDURE IF EXISTS KgfSelectNextPicker//
CREATE PROCEDURE KgfSelectNextPicker(IN pMatch INT UNSIGNED)
BEGIN
  DECLARE vNext INT UNSIGNED DEFAULT NULL;

  -- Atomic read / write
  START TRANSACTION;

  -- Select the default fallback value, the first participant
  SELECT MIN(`mp_id`)
  INTO vNext
  FROM `kgf_match_participant`
  WHERE `mp_match` = pMatch;

  -- Select the next candidate (if it exists)
  SELECT COALESCE(MIN(`mp_id`), vNext)
  INTO vNext
  FROM `kgf_match_participant`
  WHERE `mp_match` = pMatch
    AND `mp_id` > (
      SELECT `mp_id`
      FROM `kgf_match_participant`
      WHERE `mp_match` = pMatch
        AND `mp_picking` = 1
    );

  -- Set the new picker
  UPDATE `kgf_match_participant`
  SET `mp_picking` = (
    CASE WHEN `mp_id` = vNext THEN 1
         ELSE 0
    END)
  WHERE `mp_match` = pMatch;

  COMMIT;
END//

DELIMITER ;
