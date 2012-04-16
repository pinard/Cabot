<?xml version="1.0" encoding="utf-8"?>
<stylesheet version="1.0"
            xmlns="http://www.w3.org/1999/XSL/Transform"
            xmlns:fp="http://pinard.progiciels-bpi.ca">
  <import href="/home/pinard/entretien/mes-sites/commun.xsl"/>
  <output method="html" encoding="UTF-8"/>
  <template match="/">
    <call-template name="gabarit-entretien">
      <with-param name="long-package-name" select="'Personal IRC Bot'"/>
      <with-param name="logo-url" select="'/logo.png'"/>
      <with-param name="entries">

        <fp:section title="Documentation">
          <fp:entry text="README" href="/README.html"/>
        </fp:section>

        <fp:section title="Source files">
          <fp:entry text="Browse" href="https://github.com/pinard/Cabot"/>
        </fp:section>

      </with-param>
    </call-template>
  </template>
</stylesheet>
