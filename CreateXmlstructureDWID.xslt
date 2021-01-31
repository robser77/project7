<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:exsl="http://exslt.org/common"
	xmlns:str="http://exslt.org/strings"
	xmlns:set="http://exslt.org/sets"
	xmlns:date="http://exslt.org/dates-and-times"
	xmlns:math="http://exslt.org/math"
	exclude-result-prefixes="exsl str set date math func">

  <xsl:output method="xml" indent="no" encoding="utf-8"/>
  <xsl:template match="/">
    <xsl:for-each select="*">
			<trans>
				<xsl:attribute name="created">
					<xsl:value-of select="date:date-time()"/>
				</xsl:attribute>
				<startsegment include="y">UNB</startsegment>
				<endsegment include="y">UNZ</endsegment>
				<group obligatory="n" movetochild="y">
					<startsegment include="y">UNG</startsegment>
					<endsegment include="y">UNE</endsegment>
					<endsegment include="n">UNZ</endsegment>
					<doc>
						<xsl:variable name="first_node" select="name(*[1])"/>
						<xsl:variable name="last_node" select="name(*[position() = last()])"/>
						<startsegment include="y">
							<xsl:value-of select="$first_node"/>
						</startsegment>
						<endsegment include="y">
							<xsl:value-of select="$last_node"/>
						</endsegment>

						<!-- Create all groups except for summary section (UNS)  -->
						<xsl:for-each select="*[name() != 'UNS' and
																		not(preceding-sibling::*[name() = 'UNS'])]">
							<xsl:variable name="following_elems">
								<xsl:for-each select="following-sibling::*[not(preceding-sibling::*[name() = 'UNS'])]/*[1]">
									<endsegment include="n">
										<xsl:value-of select="name()"/>
									</endsegment>
								</xsl:for-each>
								<endsegment include="n">UNS</endsegment>
								<endsegment include="n">UNT</endsegment>
							</xsl:variable>
							<xsl:if test="*">
								<xsl:call-template name="create_group">
									<xsl:with-param name="following_elems" select="$following_elems"/>
								</xsl:call-template>
							</xsl:if>
						</xsl:for-each>

						<!-- Create summary section UNS group -->
						<xsl:if test="*[name() = 'UNS']">
							<uns>
								<startsegment include="y">UNS</startsegment>
								<endsegment include="n">UNT</endsegment>
								<xsl:for-each select="*[preceding-sibling::*[name() = 'UNS']]">
									<xsl:variable name="following_elems">
										<xsl:for-each select="following-sibling::*/*[1]">
											<endsegment include="n">
												<xsl:value-of select="name()"/>
											</endsegment>
										</xsl:for-each>
										<endsegment include="n">UNT</endsegment>
									</xsl:variable>
									<xsl:if test="*">
										<xsl:call-template name="create_group">
											<xsl:with-param name="following_elems" select="$following_elems"/>
										</xsl:call-template>
									</xsl:if>
								</xsl:for-each>
							</uns>
						</xsl:if>
					</doc>
				</group>
			</trans>
    </xsl:for-each>
  </xsl:template>

	<xsl:template name="create_group">
		<xsl:param name="following_elems"/>
		<xsl:variable name="group_number" select="@group"/>
		<xsl:variable name="first_segment_name" select="translate(name(*[1]),
																						'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
																						'abcdefghijklmnopqrstuvwxyz')"/>
		<xsl:variable name="segment_name" select="name(*[1])"/>
		<xsl:variable name="start_segment">
			<startsegment include="y">
				<xsl:value-of select="$segment_name"/>
			</startsegment>
		</xsl:variable>
		<xsl:variable name="end_segment">
			<endsegment include="n">
				<xsl:value-of select="$segment_name"/>
			</endsegment>
		</xsl:variable>

		<xsl:element name="{$first_segment_name}">
			<xsl:attribute name="sg">
				<xsl:value-of select="$group_number"/>
			</xsl:attribute>
			<xsl:copy-of select="$start_segment"/>
			<xsl:copy-of select="$end_segment"/>
			<xsl:copy-of select="$following_elems"/>
			<!-- build sub groups recursevely, if there are any  -->
			<xsl:for-each select="*[*]">
				<xsl:variable name="following_elems2">
					<xsl:for-each select="following-sibling::*/*[1]">
						<endsegment include="n">
							<xsl:value-of select="name()"/>
						</endsegment>
					</xsl:for-each>
					<xsl:copy-of select="$end_segment"/>
					<xsl:copy-of select="$following_elems"/>
				</xsl:variable>
				<xsl:call-template name="create_group">
					<xsl:with-param name="following_elems" select="$following_elems2"/>
				</xsl:call-template>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
</xsl:stylesheet>
