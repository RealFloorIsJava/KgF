CREATE TABLE `kgf_cards` (
  `card_id` int(12) UNSIGNED NOT NULL,
  `card_text` varchar(300) COLLATE utf8_unicode_ci NOT NULL,
  `card_type` enum('STATEMENT','OBJECT','VERB','RESERVED0','RESERVED1','RESERVED2','RESERVED3','RESERVED4') COLLATE utf8_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
ALTER TABLE `kgf_cards`
  ADD PRIMARY KEY (`card_id`);
ALTER TABLE `kgf_cards`
  MODIFY `card_id` int(12) UNSIGNED NOT NULL AUTO_INCREMENT;
