/* Football Arena – site languages. Add a language: copy the "en" block, translate it, add it to LANGS. */
(function () {
var LANGS = [["en", "English"], ["ar", "العربية"], ["fr", "Français"], ["es", "Español"], ["pt", "Português"], ["de", "Deutsch"], ["it", "Italiano"]];
var T = {
en: {live: "LIVE", nav_fix: "Matches", h_fix: "Upcoming Matches & TV Channels", fix_note: "Times are shown in your local time. TV channels can change – please check your local listings.", more_fix: "Show more matches", tv_mena: "Arab world & North Africa", tv_usa: "USA", tv_check: "Check your local TV listings", no_fix: "No matches scheduled in the next few days.",
 nav_hl: "Highlights", nav_news: "News", nav_art: "Articles", nav_quiz: "Quiz", nav_fb: "Facebook", nav_about: "About",
 tagline: "Highlights & news from the world's biggest leagues · updated every hour",
 all: "All", c_eng: "England", c_esp: "Spain", c_ita: "Italy", c_ger: "Germany", c_fra: "France", c_eur: "Europe", c_wld: "World",
 lg_eng: "Premier League", lg_esp: "LaLiga", lg_ita: "Serie A", lg_ger: "Bundesliga", lg_fra: "Ligue 1", lg_eur: "Champions League & UEFA", lg_wld: "FIFA & International",
 h_hl: "Latest Highlights", h_news: "Latest Football News", h_art: "Football Articles", see_art: "See all articles →",
 more_hl: "Show more highlights", more_news: "Show more news", none: "Nothing for this league right now – check back soon.",
 qb_t: "How well do you know football?", qb_p: "Play our quiz by country and league – learn a fun fact with every answer.", qb_btn: "Play the quiz",
 updated: "Updated", foot: "Videos play on the official YouTube channels of each league. News headlines link to the original publishers (BBC Sport, The Guardian, ESPN). All rights belong to their owners.",
 about: "About", contact: "Contact", privacy: "Privacy", ago_m: "{n} min ago", ago_h: "{n} h ago", ago_d: "{n} d ago",
 art_note: "", qz_title: "🧠 Football Quiz", qz_intro: "Pick a country or league, answer 10 questions, and learn a fun fact with every answer.",
 qz_q: "Question {i} of {n}", qz_score: "Score", qz_next: "Next question →", qz_see: "See my score", qz_ok: "Correct!", qz_no: "Not quite. The answer is",
 qz_your: "Your score", qz_m1: "Perfect! You are a football genius 🏆", qz_m2: "Great job – you really know your football! ⚽", qz_m3: "Not bad! Play again to learn more 💪",
 qz_m4: "Keep watching and reading – you'll get there! 📚", qz_again: "Play again", qz_share: "Share on Facebook",
 qz_more: "Want to learn more? Read our <a href='articles/index.html'>football articles</a> or watch the <a href='index.html#highlights'>latest highlights</a>."},
ar: {live: "مباشر", nav_fix: "المباريات", h_fix: "المباريات القادمة والقنوات الناقلة", fix_note: "المواعيد معروضة حسب توقيتك المحلي. قد تتغير القنوات الناقلة – يرجى التحقق من الدليل المحلي.", more_fix: "عرض المزيد من المباريات", tv_mena: "العالم العربي وشمال أفريقيا", tv_usa: "الولايات المتحدة", tv_check: "تحقق من دليل القنوات المحلي", no_fix: "لا توجد مباريات مقررة في الأيام القليلة القادمة.",
 nav_hl: "الملخصات", nav_news: "الأخبار", nav_art: "مقالات", nav_quiz: "اختبار", nav_fb: "فيسبوك", nav_about: "من نحن",
 tagline: "ملخصات وأخبار أكبر الدوريات في العالم · تحديث كل ساعة",
 all: "الكل", c_eng: "إنجلترا", c_esp: "إسبانيا", c_ita: "إيطاليا", c_ger: "ألمانيا", c_fra: "فرنسا", c_eur: "أوروبا", c_wld: "العالم",
 lg_eng: "الدوري الإنجليزي الممتاز", lg_esp: "الدوري الإسباني", lg_ita: "الدوري الإيطالي", lg_ger: "الدوري الألماني", lg_fra: "الدوري الفرنسي", lg_eur: "دوري الأبطال والاتحاد الأوروبي", lg_wld: "فيفا والمنتخبات",
 h_hl: "أحدث الملخصات", h_news: "آخر أخبار كرة القدم", h_art: "مقالات كرة القدم", see_art: "كل المقالات ←",
 more_hl: "عرض المزيد من الملخصات", more_news: "عرض المزيد من الأخبار", none: "لا يوجد شيء لهذا الدوري حاليًا – عد قريبًا.",
 qb_t: "ما مدى معرفتك بكرة القدم؟", qb_p: "العب اختبارنا حسب البلد والدوري – وتعلّم معلومة ممتعة مع كل إجابة.", qb_btn: "ابدأ الاختبار",
 updated: "آخر تحديث", foot: "تُعرض الفيديوهات على قنوات يوتيوب الرسمية لكل دوري. عناوين الأخبار مرتبطة بالناشرين الأصليين (BBC Sport وThe Guardian وESPN). جميع الحقوق محفوظة لأصحابها.",
 about: "من نحن", contact: "اتصل بنا", privacy: "الخصوصية", ago_m: "منذ {n} دقيقة", ago_h: "منذ {n} ساعة", ago_d: "منذ {n} يوم",
 art_note: "هذه الصفحة متوفرة باللغة الإنجليزية حاليًا.", qz_title: "🧠 اختبار كرة القدم", qz_intro: "اختر بلدًا أو دوريًا، وأجب عن 10 أسئلة، وتعلّم معلومة ممتعة مع كل إجابة.",
 qz_q: "السؤال {i} من {n}", qz_score: "النقاط", qz_next: "السؤال التالي ←", qz_see: "اعرض نتيجتي", qz_ok: "إجابة صحيحة!", qz_no: "ليس تمامًا. الإجابة الصحيحة هي",
 qz_your: "نتيجتك", qz_m1: "ممتاز! أنت عبقري كرة القدم 🏆", qz_m2: "عمل رائع – أنت تعرف كرة القدم جيدًا! ⚽", qz_m3: "ليس سيئًا! العب مجددًا لتتعلم المزيد 💪",
 qz_m4: "واصل المشاهدة والقراءة – ستنجح! 📚", qz_again: "العب مجددًا", qz_share: "شارك على فيسبوك",
 qz_more: "هل تريد معرفة المزيد؟ اقرأ <a href='articles/index.html'>مقالاتنا عن كرة القدم</a> أو شاهد <a href='index.html#highlights'>أحدث الملخصات</a>."},
fr: {live: "EN DIRECT", nav_fix: "Matchs", h_fix: "Prochains matchs & chaînes TV", fix_note: "Les horaires sont affichés à votre heure locale. Les chaînes peuvent changer – vérifiez votre programme TV local.", more_fix: "Plus de matchs", tv_mena: "Monde arabe & Afrique du Nord", tv_usa: "États-Unis", tv_check: "Vérifiez votre programme TV local", no_fix: "Aucun match prévu dans les prochains jours.",
 nav_hl: "Résumés", nav_news: "Actus", nav_art: "Articles", nav_quiz: "Quiz", nav_fb: "Facebook", nav_about: "À propos",
 tagline: "Résumés et actus des plus grands championnats du monde · mis à jour chaque heure",
 all: "Tous", c_eng: "Angleterre", c_esp: "Espagne", c_ita: "Italie", c_ger: "Allemagne", c_fra: "France", c_eur: "Europe", c_wld: "Monde",
 lg_eur: "Ligue des champions & UEFA", lg_wld: "FIFA & sélections",
 h_hl: "Derniers résumés", h_news: "Dernières actus foot", h_art: "Articles foot", see_art: "Tous les articles →",
 more_hl: "Plus de résumés", more_news: "Plus d'actus", none: "Rien pour ce championnat pour le moment – revenez bientôt.",
 qb_t: "Connaissez-vous vraiment le football ?", qb_p: "Jouez à notre quiz par pays et championnat – une anecdote à chaque réponse.", qb_btn: "Jouer au quiz",
 updated: "Mis à jour", foot: "Les vidéos sont lues sur les chaînes YouTube officielles de chaque championnat. Les titres renvoient aux éditeurs d'origine (BBC Sport, The Guardian, ESPN). Tous les droits appartiennent à leurs propriétaires.",
 about: "À propos", contact: "Contact", privacy: "Confidentialité", ago_m: "il y a {n} min", ago_h: "il y a {n} h", ago_d: "il y a {n} j",
 art_note: "Cette page est pour l'instant disponible en anglais.", qz_title: "🧠 Quiz football", qz_intro: "Choisissez un pays ou un championnat, répondez à 10 questions et découvrez une anecdote à chaque réponse.",
 qz_q: "Question {i} sur {n}", qz_score: "Score", qz_next: "Question suivante →", qz_see: "Voir mon score", qz_ok: "Bonne réponse !", qz_no: "Pas tout à fait. La réponse est",
 qz_your: "Votre score", qz_m1: "Parfait ! Vous êtes un génie du football 🏆", qz_m2: "Bravo – vous connaissez vraiment le football ! ⚽", qz_m3: "Pas mal ! Rejouez pour en apprendre plus 💪",
 qz_m4: "Continuez à regarder et à lire – vous y arriverez ! 📚", qz_again: "Rejouer", qz_share: "Partager sur Facebook",
 qz_more: "Envie d'en savoir plus ? Lisez nos <a href='articles/index.html'>articles foot</a> ou regardez les <a href='index.html#highlights'>derniers résumés</a>."},
es: {live: "EN VIVO", nav_fix: "Partidos", h_fix: "Próximos partidos y canales de TV", fix_note: "Los horarios se muestran en tu hora local. Los canales pueden cambiar – consulta tu programación local.", more_fix: "Ver más partidos", tv_mena: "Mundo árabe y norte de África", tv_usa: "EE. UU.", tv_check: "Consulta tu programación local", no_fix: "No hay partidos programados en los próximos días.",
 nav_hl: "Resúmenes", nav_news: "Noticias", nav_art: "Artículos", nav_quiz: "Quiz", nav_fb: "Facebook", nav_about: "Quiénes somos",
 tagline: "Resúmenes y noticias de las mayores ligas del mundo · actualizado cada hora",
 all: "Todos", c_eng: "Inglaterra", c_esp: "España", c_ita: "Italia", c_ger: "Alemania", c_fra: "Francia", c_eur: "Europa", c_wld: "Mundo",
 lg_eur: "Champions League y UEFA", lg_wld: "FIFA y selecciones",
 h_hl: "Últimos resúmenes", h_news: "Últimas noticias de fútbol", h_art: "Artículos de fútbol", see_art: "Ver todos los artículos →",
 more_hl: "Ver más resúmenes", more_news: "Ver más noticias", none: "Nada de esta liga por ahora – vuelve pronto.",
 qb_t: "¿Cuánto sabes de fútbol?", qb_p: "Juega a nuestro quiz por país y liga – aprende un dato curioso con cada respuesta.", qb_btn: "Jugar al quiz",
 updated: "Actualizado", foot: "Los vídeos se reproducen en los canales oficiales de YouTube de cada liga. Los titulares enlazan a los medios originales (BBC Sport, The Guardian, ESPN). Todos los derechos pertenecen a sus dueños.",
 about: "Quiénes somos", contact: "Contacto", privacy: "Privacidad", ago_m: "hace {n} min", ago_h: "hace {n} h", ago_d: "hace {n} d",
 art_note: "Por ahora esta página solo está disponible en inglés.", qz_title: "🧠 Quiz de fútbol", qz_intro: "Elige un país o una liga, responde 10 preguntas y aprende un dato curioso con cada respuesta.",
 qz_q: "Pregunta {i} de {n}", qz_score: "Puntos", qz_next: "Siguiente pregunta →", qz_see: "Ver mi resultado", qz_ok: "¡Correcto!", qz_no: "Casi. La respuesta es",
 qz_your: "Tu resultado", qz_m1: "¡Perfecto! Eres un genio del fútbol 🏆", qz_m2: "¡Muy bien, sabes mucho de fútbol! ⚽", qz_m3: "¡Nada mal! Juega otra vez para aprender más 💪",
 qz_m4: "Sigue viendo y leyendo – ¡lo conseguirás! 📚", qz_again: "Jugar otra vez", qz_share: "Compartir en Facebook",
 qz_more: "¿Quieres saber más? Lee nuestros <a href='articles/index.html'>artículos de fútbol</a> o mira los <a href='index.html#highlights'>últimos resúmenes</a>."},
pt: {live: "AO VIVO", nav_fix: "Jogos", h_fix: "Próximos jogos e canais de TV", fix_note: "Os horários aparecem no seu fuso local. Os canais podem mudar – confira a programação local.", more_fix: "Ver mais jogos", tv_mena: "Mundo árabe e Norte da África", tv_usa: "EUA", tv_check: "Confira a programação local", no_fix: "Nenhum jogo marcado para os próximos dias.",
 nav_hl: "Melhores momentos", nav_news: "Notícias", nav_art: "Artigos", nav_quiz: "Quiz", nav_fb: "Facebook", nav_about: "Sobre",
 tagline: "Melhores momentos e notícias das maiores ligas do mundo · atualizado a cada hora",
 all: "Todos", c_eng: "Inglaterra", c_esp: "Espanha", c_ita: "Itália", c_ger: "Alemanha", c_fra: "França", c_eur: "Europa", c_wld: "Mundo",
 lg_eur: "Champions League e UEFA", lg_wld: "FIFA e seleções",
 h_hl: "Últimos melhores momentos", h_news: "Últimas notícias de futebol", h_art: "Artigos de futebol", see_art: "Ver todos os artigos →",
 more_hl: "Ver mais vídeos", more_news: "Ver mais notícias", none: "Nada desta liga por enquanto – volte em breve.",
 qb_t: "Quanto você sabe de futebol?", qb_p: "Jogue nosso quiz por país e liga – aprenda uma curiosidade a cada resposta.", qb_btn: "Jogar o quiz",
 updated: "Atualizado", foot: "Os vídeos são reproduzidos nos canais oficiais do YouTube de cada liga. As manchetes levam aos veículos originais (BBC Sport, The Guardian, ESPN). Todos os direitos pertencem aos seus donos.",
 about: "Sobre", contact: "Contato", privacy: "Privacidade", ago_m: "há {n} min", ago_h: "há {n} h", ago_d: "há {n} d",
 art_note: "Por enquanto esta página está disponível apenas em inglês.", qz_title: "🧠 Quiz de futebol", qz_intro: "Escolha um país ou uma liga, responda 10 perguntas e aprenda uma curiosidade a cada resposta.",
 qz_q: "Pergunta {i} de {n}", qz_score: "Pontos", qz_next: "Próxima pergunta →", qz_see: "Ver meu resultado", qz_ok: "Correto!", qz_no: "Quase. A resposta é",
 qz_your: "Seu resultado", qz_m1: "Perfeito! Você é um gênio do futebol 🏆", qz_m2: "Muito bem – você entende de futebol! ⚽", qz_m3: "Nada mal! Jogue de novo para aprender mais 💪",
 qz_m4: "Continue assistindo e lendo – você chega lá! 📚", qz_again: "Jogar de novo", qz_share: "Compartilhar no Facebook",
 qz_more: "Quer saber mais? Leia nossos <a href='articles/index.html'>artigos de futebol</a> ou assista aos <a href='index.html#highlights'>últimos melhores momentos</a>."},
de: {live: "LIVE", nav_fix: "Spiele", h_fix: "Nächste Spiele & TV-Sender", fix_note: "Die Zeiten werden in deiner Ortszeit angezeigt. TV-Sender können sich ändern – bitte prüfe dein lokales TV-Programm.", more_fix: "Mehr Spiele", tv_mena: "Arabische Welt & Nordafrika", tv_usa: "USA", tv_check: "Bitte lokales TV-Programm prüfen", no_fix: "In den nächsten Tagen sind keine Spiele angesetzt.",
 nav_hl: "Highlights", nav_news: "News", nav_art: "Artikel", nav_quiz: "Quiz", nav_fb: "Facebook", nav_about: "Über uns",
 tagline: "Highlights und News aus den größten Ligen der Welt · stündlich aktualisiert",
 all: "Alle", c_eng: "England", c_esp: "Spanien", c_ita: "Italien", c_ger: "Deutschland", c_fra: "Frankreich", c_eur: "Europa", c_wld: "Welt",
 lg_eur: "Champions League & UEFA", lg_wld: "FIFA & Nationalteams",
 h_hl: "Neueste Highlights", h_news: "Neueste Fußball-News", h_art: "Fußball-Artikel", see_art: "Alle Artikel →",
 more_hl: "Mehr Highlights", more_news: "Mehr News", none: "Gerade nichts zu dieser Liga – schau bald wieder vorbei.",
 qb_t: "Wie gut kennst du dich im Fußball aus?", qb_p: "Spiel unser Quiz nach Land und Liga – mit einem spannenden Fakt zu jeder Antwort.", qb_btn: "Quiz spielen",
 updated: "Aktualisiert", foot: "Die Videos laufen auf den offiziellen YouTube-Kanälen der Ligen. Die Schlagzeilen verlinken auf die ursprünglichen Medien (BBC Sport, The Guardian, ESPN). Alle Rechte liegen bei den Eigentümern.",
 about: "Über uns", contact: "Kontakt", privacy: "Datenschutz", ago_m: "vor {n} Min.", ago_h: "vor {n} Std.", ago_d: "vor {n} T.",
 art_note: "Diese Seite ist derzeit nur auf Englisch verfügbar.", qz_title: "🧠 Fußball-Quiz", qz_intro: "Wähle ein Land oder eine Liga, beantworte 10 Fragen und lerne zu jeder Antwort einen spannenden Fakt.",
 qz_q: "Frage {i} von {n}", qz_score: "Punkte", qz_next: "Nächste Frage →", qz_see: "Mein Ergebnis", qz_ok: "Richtig!", qz_no: "Nicht ganz. Die Antwort ist",
 qz_your: "Dein Ergebnis", qz_m1: "Perfekt! Du bist ein Fußball-Genie 🏆", qz_m2: "Super – du kennst dich richtig gut aus! ⚽", qz_m3: "Nicht schlecht! Spiel nochmal und lerne mehr 💪",
 qz_m4: "Weiter schauen und lesen – du schaffst das! 📚", qz_again: "Nochmal spielen", qz_share: "Auf Facebook teilen",
 qz_more: "Mehr erfahren? Lies unsere <a href='articles/index.html'>Fußball-Artikel</a> oder schau die <a href='index.html#highlights'>neuesten Highlights</a>."},
it: {live: "LIVE", nav_fix: "Partite", h_fix: "Prossime partite e canali TV", fix_note: "Gli orari sono nel tuo fuso orario. I canali possono cambiare – controlla la guida TV locale.", more_fix: "Altre partite", tv_mena: "Mondo arabo e Nord Africa", tv_usa: "USA", tv_check: "Controlla la guida TV locale", no_fix: "Nessuna partita in programma nei prossimi giorni.",
 nav_hl: "Highlights", nav_news: "Notizie", nav_art: "Articoli", nav_quiz: "Quiz", nav_fb: "Facebook", nav_about: "Chi siamo",
 tagline: "Highlights e notizie dai più grandi campionati del mondo · aggiornato ogni ora",
 all: "Tutti", c_eng: "Inghilterra", c_esp: "Spagna", c_ita: "Italia", c_ger: "Germania", c_fra: "Francia", c_eur: "Europa", c_wld: "Mondo",
 lg_eur: "Champions League e UEFA", lg_wld: "FIFA e nazionali",
 h_hl: "Ultimi highlights", h_news: "Ultime notizie di calcio", h_art: "Articoli di calcio", see_art: "Tutti gli articoli →",
 more_hl: "Altri highlights", more_news: "Altre notizie", none: "Niente per questo campionato al momento – torna presto.",
 qb_t: "Quanto ne sai di calcio?", qb_p: "Gioca al nostro quiz per paese e campionato – scopri una curiosità a ogni risposta.", qb_btn: "Gioca al quiz",
 updated: "Aggiornato", foot: "I video si guardano sui canali YouTube ufficiali di ogni campionato. I titoli rimandano alle testate originali (BBC Sport, The Guardian, ESPN). Tutti i diritti appartengono ai rispettivi proprietari.",
 about: "Chi siamo", contact: "Contatti", privacy: "Privacy", ago_m: "{n} min fa", ago_h: "{n} h fa", ago_d: "{n} g fa",
 art_note: "Per ora questa pagina è disponibile solo in inglese.", qz_title: "🧠 Quiz di calcio", qz_intro: "Scegli un paese o un campionato, rispondi a 10 domande e scopri una curiosità a ogni risposta.",
 qz_q: "Domanda {i} di {n}", qz_score: "Punti", qz_next: "Domanda successiva →", qz_see: "Vedi il mio punteggio", qz_ok: "Esatto!", qz_no: "Non proprio. La risposta è",
 qz_your: "Il tuo punteggio", qz_m1: "Perfetto! Sei un genio del calcio 🏆", qz_m2: "Ottimo – di calcio ne sai davvero! ⚽", qz_m3: "Non male! Gioca ancora per imparare di più 💪",
 qz_m4: "Continua a guardare e leggere – ce la farai! 📚", qz_again: "Gioca ancora", qz_share: "Condividi su Facebook",
 qz_more: "Vuoi saperne di più? Leggi i nostri <a href='articles/index.html'>articoli di calcio</a> o guarda gli <a href='index.html#highlights'>ultimi highlights</a>."}
};

function pick() {
  var s = null;
  try { s = localStorage.getItem("fa_lang"); } catch (e) {}
  if (s && T[s]) return s;
  var n = (navigator.language || "en").slice(0, 2).toLowerCase();
  return T[n] ? n : "en";
}
var FA = window.FA = {lang: pick(), langs: LANGS,
  t: function (k, v) {
    var s = (T[FA.lang] && T[FA.lang][k]); if (s == null) s = T.en[k]; if (s == null) s = k;
    for (var x in (v || {})) s = s.split("{" + x + "}").join(v[x]);
    return s;
  },
  ago: function (t) {
    var s = Date.now() / 1000 - t;
    if (s < 3600) return FA.t("ago_m", {n: Math.max(1, Math.floor(s / 60))});
    if (s < 86400) return FA.t("ago_h", {n: Math.floor(s / 3600)});
    return FA.t("ago_d", {n: Math.floor(s / 86400)});
  },
  apply: function () {
    var root = document.documentElement;
    root.lang = FA.lang; root.dir = FA.lang === "ar" ? "rtl" : "ltr";
    document.querySelectorAll("[data-i18n]").forEach(function (e) { e.textContent = FA.t(e.dataset.i18n); });
    document.querySelectorAll("[data-i18n-html]").forEach(function (e) { e.innerHTML = FA.t(e.dataset.i18nHtml); });
    document.querySelectorAll("[data-i18n-note]").forEach(function (e) { var s = FA.t("art_note"); e.textContent = s; e.style.display = s ? "" : "none"; });
    document.querySelectorAll(".ago[data-t]").forEach(function (e) { e.textContent = FA.ago(+e.dataset.t); });
    var loc = FA.lang === "ar" ? "ar-MA" : FA.lang;
    document.querySelectorAll(".ftime[data-k]").forEach(function (e) {
      var d = new Date(+e.dataset.k * 1000);
      try { e.textContent = d.toLocaleDateString(loc, {weekday: "long", day: "numeric", month: "long"}) + " · " + d.toLocaleTimeString(loc, {hour: "2-digit", minute: "2-digit"}); } catch (x) {}
    });
    document.querySelectorAll(".langpick").forEach(function (s) { s.value = FA.lang; });
  },
  set: function (l) {
    FA.lang = T[l] ? l : "en";
    try { localStorage.setItem("fa_lang", FA.lang); } catch (e) {}
    FA.apply();
    document.dispatchEvent(new Event("fa:lang"));
  }
};
document.querySelectorAll(".langpick").forEach(function (s) {
  s.innerHTML = LANGS.map(function (l) { return '<option value="' + l[0] + '">' + l[1] + "</option>"; }).join("");
  s.onchange = function () { FA.set(s.value); };
});
FA.apply();
})();
