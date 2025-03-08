<?php

class PhoneticTranscription {
    // Dictionnaire de correspondances phonétiques
    private static $phonemes = [
        'a' => 'a', 'à' => 'a', 'â' => 'a',
        'e' => 'ə', 'é' => 'e', 'è' => 'ɛ', 'ê' => 'ɛ',
        'i' => 'i', 'î' => 'i',
        'o' => 'ɔ', 'ô' => 'o',
        'u' => 'y', 'û' => 'y',
        'ou' => 'u',
        'an' => 'ɑ̃', 'en' => 'ɑ̃',
        'in' => 'ɛ̃', 'ain' => 'ɛ̃', 'ein' => 'ɛ̃',
        'on' => 'ɔ̃',
        'ch' => 'ʃ',
        'gn' => 'ɲ',
        'ng' => 'ŋ',
        'ph' => 'f',
        'th' => 't',
        'qu' => 'k',
        'gu' => 'g'
    ];

    /**
     * Initialise l'extension lors du premier appel du parser
     */
    public static function onParserFirstCallInit(Parser $parser) {
        $parser->setFunctionHook('phonetic', [self::class, 'renderPhonetic']);
        return true;
    }

    /**
     * Fonction de rendu pour la transcription phonétique
     */
    public static function renderPhonetic($parser, $text = '') {
        // Configuration
        $config = MediaWikiServices::getInstance()->getConfigFactory()
            ->makeConfig('PhoneticTranscription');
        
        // Transcription
        $transcription = self::transcribeText($text);
        
        // Rendu HTML
        $output = Html::element('span', 
            ['class' => 'phonetic-transcription'], 
            '[' . $transcription . ']'
        );
        
        return [
            $output,
            'noparse' => true,
            'isHTML' => true
        ];
    }

    /**
     * Transcrit le texte en phonèmes
     */
    private static function transcribeText($text) {
        $text = mb_strtolower($text);
        
        // Trier les patterns par longueur décroissante
        $patterns = array_keys(self::$phonemes);
        usort($patterns, function($a, $b) {
            return strlen($b) - strlen($a);
        });
        
        // Appliquer les remplacements
        foreach ($patterns as $pattern) {
            $phoneme = self::$phonemes[$pattern];
            $text = str_replace($pattern, $phoneme, $text);
        }
        
        return $text;
    }
} 