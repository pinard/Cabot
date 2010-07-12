<?xml version="1.0" encoding="utf-8"?>
<stylesheet version="1.0"
            xmlns="http://www.w3.org/1999/XSL/Transform">
  <import href="/home/pinard/entretien/mes-sites/commun.xsl"/>
  <output method="html" encoding="UTF-8"/>
  <template match="/">
    <call-template name="gabarit-entretien">
      <with-param name="long-package-name" select="'Personal IRC Bot'"/>
      <with-param name="style-url" select="'/gabarit.css'"/>
      <with-param name="logo-url" select="'/logo.png'"/>
      <with-param name="README" select="'/README.html'"/>
      <with-param name="Browse" select="'http://github.com/pinard/Cabot'"/>
    </call-template>
  </template>
</stylesheet>
