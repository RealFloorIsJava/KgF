CREATE TABLE `kgf_cards` (
  `card_id` int(12) UNSIGNED NOT NULL,
  `card_text` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `card_type` enum('STATEMENT','OBJECT','VERB') COLLATE utf8_unicode_ci NOT NULL,
  `card_match_id` int(12) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE `kgf_hand` (
  `hand_id` int(12) UNSIGNED NOT NULL,
  `hand_participant` int(12) UNSIGNED NOT NULL,
  `hand_card` int(12) UNSIGNED NOT NULL,
  `hand_pick` tinyint(3) UNSIGNED DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE `kgf_match` (
  `match_id` int(12) UNSIGNED NOT NULL,
  `match_timer` bigint(12) UNSIGNED NOT NULL,
  `match_card_id` int(12) UNSIGNED DEFAULT NULL,
  `match_state` enum('PENDING','CHOOSING','PICKING','COOLDOWN','ENDING') COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE `kgf_match_chat` (
  `chat_id` int(12) UNSIGNED NOT NULL,
  `chat_match_id` int(12) UNSIGNED NOT NULL,
  `chat_type` enum('SYSTEM','USER') COLLATE utf8_unicode_ci NOT NULL,
  `chat_message` text COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE `kgf_match_participant` (
  `mp_id` int(12) UNSIGNED NOT NULL,
  `mp_player` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `mp_name` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `mp_match` int(12) UNSIGNED NOT NULL,
  `mp_score` int(12) UNSIGNED NOT NULL,
  `mp_picking` tinyint(1) UNSIGNED NOT NULL,
  `mp_timeout` bigint(12) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `kgf_cards`
  ADD PRIMARY KEY (`card_id`),
  ADD KEY `card_match_id` (`card_match_id`);

ALTER TABLE `kgf_hand`
  ADD PRIMARY KEY (`hand_id`),
  ADD KEY `hand_participant` (`hand_participant`),
  ADD KEY `hand_card` (`hand_card`);

ALTER TABLE `kgf_match`
  ADD PRIMARY KEY (`match_id`),
  ADD KEY `match_card_id` (`match_card_id`);

ALTER TABLE `kgf_match_chat`
  ADD PRIMARY KEY (`chat_id`),
  ADD KEY `chat_match_id` (`chat_match_id`);

ALTER TABLE `kgf_match_participant`
  ADD PRIMARY KEY (`mp_id`),
  ADD KEY `mp_match` (`mp_match`);

ALTER TABLE `kgf_cards`
  MODIFY `card_id` int(12) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `kgf_hand`
  MODIFY `hand_id` int(12) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `kgf_match`
  MODIFY `match_id` int(12) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `kgf_match_chat`
  MODIFY `chat_id` int(12) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `kgf_match_participant`
  MODIFY `mp_id` int(12) UNSIGNED NOT NULL AUTO_INCREMENT;

ALTER TABLE `kgf_cards`
  ADD CONSTRAINT `kgf_cards_ibfk_1` FOREIGN KEY (`card_match_id`) REFERENCES `kgf_match` (`match_id`) ON DELETE CASCADE;

ALTER TABLE `kgf_hand`
  ADD CONSTRAINT `kgf_hand_ibfk_1` FOREIGN KEY (`hand_participant`) REFERENCES `kgf_match_participant` (`mp_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `kgf_hand_ibfk_2` FOREIGN KEY (`hand_card`) REFERENCES `kgf_cards` (`card_id`) ON DELETE CASCADE;

ALTER TABLE `kgf_match`
  ADD CONSTRAINT `kgf_match_ibfk_1` FOREIGN KEY (`match_card_id`) REFERENCES `kgf_cards` (`card_id`) ON DELETE CASCADE;

ALTER TABLE `kgf_match_chat`
  ADD CONSTRAINT `kgf_match_chat_ibfk_1` FOREIGN KEY (`chat_match_id`) REFERENCES `kgf_match` (`match_id`) ON DELETE CASCADE;

ALTER TABLE `kgf_match_participant`
  ADD CONSTRAINT `kgf_match_participant_ibfk_1` FOREIGN KEY (`mp_match`) REFERENCES `kgf_match` (`match_id`) ON DELETE CASCADE;
