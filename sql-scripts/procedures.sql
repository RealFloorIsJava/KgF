DELIMITER //

DROP PROCEDURE IF EXISTS ReplenishMatch//
CREATE PROCEDURE ReplenishMatch(IN pMatch INT UNSIGNED)
BEGIN
  CALL ReplenishMatchType(pMatch, 'OBJECT');
  CALL ReplenishMatchType(pMatch, 'VERB');
END//

DROP PROCEDURE IF EXISTS ReplenishMatchType//
CREATE PROCEDURE ReplenishMatchType(IN pMatch INT UNSIGNED,
  IN pType ENUM('STATEMENT', 'OBJECT', 'VERB'))
BEGIN
  DECLARE vDone INT DEFAULT 0;
  DECLARE vPartId INT UNSIGNED;
  DECLARE vCur CURSOR FOR
    SELECT `mp_id`
    FROM `kgf_match_participant`
    WHERE `mp_match` = pMatch;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET vDone = 1;

  OPEN vCur;
  REPEAT
    FETCH vCur INTO vPartId;
    IF NOT vDone THEN
      CALL ReplenishHandCards(vPartId, pType);
    END IF;
  UNTIL vDone END REPEAT;
  CLOSE vCur;
END//

DROP PROCEDURE IF EXISTS ReplenishHandCards//
CREATE PROCEDURE ReplenishHandCards(IN pParticipant INT UNSIGNED,
  IN pType ENUM('STATEMENT', 'OBJECT', 'VERB'))
BEGIN
  DECLARE vMaxCards INT UNSIGNED DEFAULT 6;
  DECLARE vNeedCards INT UNSIGNED;

  SELECT vMaxCards - COUNT(*)
  INTO vNeedCards
  FROM `kgf_hand`
    JOIN `kgf_cards` ON (`card_id` = `hand_card`)
  WHERE `hand_participant` = pParticipant
    AND `card_type` = pType;

  INSERT INTO `kgf_hand`
    (`hand_id`, `hand_participant`, `hand_card`, `hand_choice`)
    SELECT NULL, pParticipant, `card_id`, NULL
    FROM `kgf_cards`
    WHERE `card_id` NOT IN (
        SELECT `hand_card`
        FROM `kgf_hand`
        WHERE `hand_participant` = pParticipant
      ) AND `card_type` = pType
    ORDER BY RAND()
    LIMIT vNeedCards;
END//

DELIMITER ;
