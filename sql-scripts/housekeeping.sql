DELIMITER //

/**
 * Performs housekeeping tasks on the database
 */
DROP PROCEDURE IF EXISTS KgfPerformHousekeeping//
CREATE PROCEDURE KgfPerformHousekeeping()
BEGIN
  -- Use a transaction so that every timeout is announced at most once
  START TRANSACTION;

  -- Write a timeout notice for every participant after their timeout
  INSERT INTO `kgf_match_chat`
    (`chat_id`, `chat_match_id`, `chat_type`, `chat_message`)
    SELECT NULL, `mp_match`, 'SYSTEM',
      CONCAT('<b>', `mp_name`, ' timed out.</b>')
    FROM `kgf_match_participant`
    WHERE `mp_timeout` <= UNIX_TIMESTAMP();

  -- Delete participants after their timeout
  DELETE FROM `kgf_match_participant`
  WHERE `mp_timeout` <= UNIX_TIMESTAMP();

  COMMIT;

  -- Delete empty matches
  DELETE FROM `kgf_match`
  WHERE (
      SELECT COUNT(*)
      FROM `kgf_match_participant`
      WHERE `mp_match` = `match_id`
    ) < 1;
END//

DELIMITER ;
