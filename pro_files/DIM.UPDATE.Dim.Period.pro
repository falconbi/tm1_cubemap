601,100
602,"DIM.UPDATE.Dim.Period"
562,"NULL"
586,
585,
564,
565,"mA[kzT[AvSNIpayZO>O<13J123JSvqEzKoY@LakhHta_MjuFC8etLi8R@JOx<juvqolV\j9H:hvdd37xy@pBCqf0mYibS:FP4[sy<oi34J2Fz3Ds\aF_gBCD\L]]>z`Yydml1y=M_2Qky^\GPQKxMJNQ_pf`vKH8m_]M>D32NK2klf`tC`?moD7d1RO=lBqQx9sKx415"
559,1
928,0
593,
594,
595,
597,
598,
596,
800,
801,
566,0
567,","
588,"."
589,
568,""""
570,
571,
569,0
592,0
599,1000
560,7
pStartYear
pEndYear
pStartMonth
pPeriodDimName
pDeleteAndRebuild
pIncludeDriverElement
pIncludeInputElement
561,7
2
2
2
2
2
2
2
590,7
pStartYear,"2011"
pEndYear,"2040"
pStartMonth,"Jan"
pPeriodDimName,"Period"
pDeleteAndRebuild,"N"
pIncludeDriverElement,"N"
pIncludeInputElement,"N"
637,7
pStartYear,""
pEndYear,""
pStartMonth,""
pPeriodDimName,""
pDeleteAndRebuild,""
pIncludeDriverElement,""
pIncludeInputElement,""
577,0
578,0
579,0
580,0
581,0
582,0
603,0
572,542

#****Begin: Generated Statements***
#****End: Generated Statements****

#GENERALCOMMENT
#DATASOURCECOMMENT
#PROLOGCOMMENT
#METADATACOMMENT
#DATACOMMENT
#EPILOGCOMMENT 


#########################################################
## Define Constants and Variables                  
#########################################################

cDimName =	pPeriodDimName;
cProcessName = 	GetProcessName( );
cTimeStamp = 	TimSt( Now, '\Y\m\d\h\i\s' );
cErrorDirectory =	GetProcessErrorFileDirectory;
cSubsetZero = 	'SubsetZero';
cSubsetBuild =	'SubsetBuild';
cViewZero = 	'ViewZero';
cViewBuild = 	'ViewBuild';


sTopConsol =	cDimName | ' Consolidations';
sRepConsol =	'Reporting';
sSysConsol =	'System';

sFYConsol =	'All FY';
sQTRConsol =	'All QTR';
sYTDConsol =	'All YTD';
sYTGConsol =	'All YTG';
sLTDConsol =	'All LTD';

IF(pIncludeDriverElement@='Y');
	sDriverConsol =     'All Driver';
ENDIF;
IF(pIncludeInputElement@='Y');
	sInputConsol =      'All Input';
ENDIF;

sNo =		 'No '|cDimName;

sCaptionAttr =	'Caption';
sNextPeriodAttr =	'Next Period';
sPrevPeriodAttr =	'Previous Period';
sNextYearAttr =	'Next Year';
sPrevYearAttr =	'Previous Year';
sLastPeriodAttr =	'Last Period';
sFirstPeriodAttr =	'First Period';
sMonthActualsAttr = 'Month Contains Actuals';
sLongNameAttr =	'Long Name';
sYearNameAttr =	'Year Name' ;
sFinYearAttr =	'FinYear' ;
sMonthAttr =	'Month' ;


IF(DimensionExists(cDimName) = 0);
	DimensionCreate(cDimName);
ENDIF;

IF(pDeleteAndRebuild@='Y');
	DimensionDeleteAllElements(cDimName);
ENDIF;

#########################################################
## Parameters                                                 
#########################################################
# pStartYear = A financial period start point e.g. 2014
# pEndYear = A financial period end point e.g. 2016
# pStartMonth = A financial period which indicates the start of the Financial Year e.g. Jul
# With the above parameters Elements for the 2014, 2015, 2016 Fiscal years will be created
# Period 01 - 12 will be inserted under each Fiscal year. Period 01 will have the Alias of Jul

sStartYear =    pStartYear;
sEndYear =      pEndYear;
sStartMonth =   pStartMonth;
nStartYear =    StringToNumber(sStartYear); 
nEndYear =      StringToNumber(sEndYear);

#--Validate Parameter Inputs
# Errorout with warning if incorrect parameter is specified
# TBC

sStartYearCheck = Long(sStartYear);
IF(sStartYearCheck <> 4);
	nBreakFlag =1;
	ItemReject('Please Enter a Year in YYYY format. e.g. 2014');
ENDIF;

sEndYearCheck = Long(sEndYear);
IF(sEndYearCheck <> 4);
	nBreakFlag =1;
	ItemReject('Please Enter a Year in YYYY format. e.g. 2030');
ENDIF;

sStartMonthCheck = Long(sStartMonth);
IF(sStartMonthCheck <> 3);
	nBreakFlag =1;
	ItemReject('Please Enter a Month in mmm format. e.g. Jul');
ENDIF;

sOrderCheck1 = nStartYear; 
sOrderCheck2 = nEndYear;
IF(sOrderCheck1>= sOrderCheck2);
	nBreakFlag =1;
	ItemReject('Please Enter a StartYear less than EndYear');
ENDIF;
# Validate Parameter Inputs
IF(nBreakFlag = 1);
	ProcessError;
ENDIF;

#########################################################
## Unravel the dimension (call external process)                      
#########################################################

sProcessName = 'Bedrock.Dim.Hierarchy.Unwind.Consolidation';

IF(DimIx(cDimName, sFYConsol) > 0);
	ExecuteProcess(sProcessName,'pDimension',cDimName,'pConsol',sFYConsol,'pRecursive',1,'pDebug',0);
ENDIF;
IF(DimIx(cDimName, sQTRConsol) > 0);
	ExecuteProcess(sProcessName,'pDimension',cDimName,'pConsol',sQTRConsol,'pRecursive',1,'pDebug',0);
ENDIF;
IF(DimIx(cDimName, sYTDConsol) > 0);
	ExecuteProcess(sProcessName,'pDimension',cDimName,'pConsol',sYTDConsol,'pRecursive',1,'pDebug',0);
ENDIF;
IF(DimIx(cDimName, sYTGConsol) > 0);
	ExecuteProcess(sProcessName,'pDimension',cDimName,'pConsol',sYTGConsol,'pRecursive',1,'pDebug',0);
ENDIF;
IF(DimIx(cDimName, sLTDConsol) > 0);
	ExecuteProcess(sProcessName,'pDimension',cDimName,'pConsol',sLTDConsol,'pRecursive',1,'pDebug',0);
ENDIF;
IF(DimIx(cDimName, sDriverConsol) > 0);
	ExecuteProcess(sProcessName,'pDimension',cDimName,'pConsol',sDriverConsol,'pRecursive',1,'pDebug',0);
ENDIF;
IF(DimIx(cDimName, sInputConsol) > 0);
	ExecuteProcess(sProcessName,'pDimension',cDimName,'pConsol',sInputConsol,'pRecursive',1,'pDebug',0);
ENDIF;

#########################################################
## Insert Attributes                                                                    
#########################################################

#Insert Period Specific Attributes
AttrInsert(cDimName,'', sCaptionAttr,'A');
AttrInsert(cDimName,'', sLongNameAttr,'A');
AttrInsert(cDimName,'', sNextPeriodAttr,'S');
AttrInsert(cDimName,'', sPrevPeriodAttr,'S');
AttrInsert(cDimName,'', sNextYearAttr,'S');
AttrInsert(cDimName,'', sPrevYearAttr,'S');
AttrInsert(cDimName,'', sLastPeriodAttr,'S');
AttrInsert(cDimName,'', sFirstPeriodAttr,'S');
AttrInsert(cDimName,'', sMonthActualsAttr,'N');
AttrInsert(cDimName,'', sYearNameAttr,'S');
AttrInsert(cDimName,'', sFinYearAttr,'S');
AttrInsert(cDimName,'', sMonthAttr,'S');

#########################################################
## Disable cube logging      
#########################################################
cCube = '}ElementAttributes_'| cDimName;
cCubeLogging = CubeGetLogChanges(cCube);
CubeSetLogChanges(cCube, 0);  


#########################################################
## Clear Existing Attributes Values                                                   
#########################################################

sAttributeCube = '}ElementAttributes_'| cDimName;
CubeClearData( sAttributeCube );

#########################################################
## Insert System / Top level Elements                                               
#########################################################

DimensionElementInsert(cDimName,'',sTopConsol,'C');

DimensionElementInsert(cDimName,'',sRepConsol,'C');
DimensionElementComponentAdd(cDimName,sTopConsol,sRepConsol,0);

DimensionElementInsert(cDimName,'',sSysConsol,'C');
DimensionElementComponentAdd(cDimName,sTopConsol,sSysConsol,0);

DimensionElementInsert(cDimName,'',sFYConsol,'C');
DimensionElementComponentAdd(cDimName,sRepConsol,sFYConsol,1);

DimensionElementInsert(cDimName,'',sQTRConsol,'C');
DimensionElementComponentAdd(cDimName,sRepConsol,sQTRConsol,1);

DimensionElementInsert(cDimName,'',sYTDConsol,'C');
DimensionElementComponentAdd(cDimName,sRepConsol,sYTDConsol,1);

DimensionElementInsert(cDimName,'',sYTGConsol,'C');
DimensionElementComponentAdd(cDimName,sRepConsol,sYTGConsol,1);

DimensionElementInsert(cDimName,'',sLTDConsol,'C');
DimensionElementComponentAdd(cDimName,sRepConsol,sLTDConsol,1);

IF(pIncludeDriverElement@='Y');
	DimensionElementInsert(cDimName,'',sDriverConsol,'C');
	DimensionElementComponentAdd(cDimName,sRepConsol,sDriverConsol,1);
ENDIF;
IF(pIncludeInputElement@='Y');
	DimensionElementInsert(cDimName,'',sInputConsol,'C');
	DimensionElementComponentAdd(cDimName,sRepConsol,sInputConsol,1);
ENDIF;
DimensionElementInsert(cDimName,'',sNo,'N');
DimensionElementComponentAdd(cDimName,sSysConsol,sNo,1);


#########################################################
## Create Tempoary Dimension To Lookup Next / Prev Month
#########################################################
sControlDimension = '}' | cDimName | '_Control' ;

IF(DimensionExists(sControlDimension)=1);
	DimensionDestroy(sControlDimension);
ENDIF;

# Create Dimension
DimensionCreate(sControlDimension);

# Insert Attributes
AttrInsert(sControlDimension,'',sNextPeriodAttr,'S');
AttrInsert(sControlDimension,'',sPrevPeriodAttr,'S');
AttrInsert(sControlDimension,'', sLongNameAttr,'S');

# Insert Elements
DimensionElementInsertDirect(sControlDimension,'','Jan','N');
DimensionElementInsertDirect(sControlDimension,'','Feb','N');
DimensionElementInsertDirect(sControlDimension,'','Mar','N');
DimensionElementInsertDirect(sControlDimension,'','Apr','N');
DimensionElementInsertDirect(sControlDimension,'','May','N');
DimensionElementInsertDirect(sControlDimension,'','Jun','N');
DimensionElementInsertDirect(sControlDimension,'','Jul','N');
DimensionElementInsertDirect(sControlDimension,'','Aug','N');
DimensionElementInsertDirect(sControlDimension,'','Sep','N');
DimensionElementInsertDirect(sControlDimension,'','Oct','N');
DimensionElementInsertDirect(sControlDimension,'','Nov','N');
DimensionElementInsertDirect(sControlDimension,'','Dec','N');
DimensionElementInsertDirect(sControlDimension,'','Jan1','N');
DimensionElementInsertDirect(sControlDimension,'','Feb1','N');
DimensionElementInsertDirect(sControlDimension,'','Mar1','N');
DimensionElementInsertDirect(sControlDimension,'','Apr1','N');
DimensionElementInsertDirect(sControlDimension,'','May1','N');
DimensionElementInsertDirect(sControlDimension,'','Jun1','N');
DimensionElementInsertDirect(sControlDimension,'','Jul1','N');
DimensionElementInsertDirect(sControlDimension,'','Aug1','N');
DimensionElementInsertDirect(sControlDimension,'','Sep1','N');
DimensionElementInsertDirect(sControlDimension,'','Oct1','N');
DimensionElementInsertDirect(sControlDimension,'','Nov1','N');
DimensionElementInsertDirect(sControlDimension,'','Dec1','N');

# Insert Attributes

AttrPutS('Feb',sControlDimension,'Jan',sNextPeriodAttr);
AttrPutS('Dec',sControlDimension,'Jan',sPrevPeriodAttr);
AttrPutS('January',sControlDimension,'Jan',sLongNameAttr);

AttrPutS('Mar',sControlDimension,'Feb',sNextPeriodAttr);
AttrPutS('Jan',sControlDimension,'Feb',sPrevPeriodAttr);
AttrPutS('February',sControlDimension,'Feb',sLongNameAttr);

AttrPutS('Apr',sControlDimension,'Mar',sNextPeriodAttr);
AttrPutS('Feb',sControlDimension,'Mar',sPrevPeriodAttr);
AttrPutS('March',sControlDimension,'Mar',sLongNameAttr);

AttrPutS('May',sControlDimension,'Apr',sNextPeriodAttr);
AttrPutS('Mar',sControlDimension,'Apr',sPrevPeriodAttr);
AttrPutS('April',sControlDimension,'Apr',sLongNameAttr);

AttrPutS('Jun',sControlDimension,'May',sNextPeriodAttr);
AttrPutS('Apr',sControlDimension,'May',sPrevPeriodAttr);
AttrPutS('May',sControlDimension,'May',sLongNameAttr);

AttrPutS('Jul',sControlDimension,'Jun',sNextPeriodAttr);
AttrPutS('May',sControlDimension,'Jun',sPrevPeriodAttr);
AttrPutS('June',sControlDimension,'Jun',sLongNameAttr);

AttrPutS('Aug',sControlDimension,'Jul',sNextPeriodAttr);
AttrPutS('Jun',sControlDimension,'Jul',sPrevPeriodAttr);
AttrPutS('July',sControlDimension,'Jul',sLongNameAttr);

AttrPutS('Sep',sControlDimension,'Aug',sNextPeriodAttr);
AttrPutS('Jul',sControlDimension,'Aug',sPrevPeriodAttr);
AttrPutS('August',sControlDimension,'Aug',sLongNameAttr);

AttrPutS('Oct',sControlDimension,'Sep',sNextPeriodAttr);
AttrPutS('Aug',sControlDimension,'Sep',sPrevPeriodAttr);
AttrPutS('September',sControlDimension,'Sep',sLongNameAttr);

AttrPutS('Nov',sControlDimension,'Oct',sNextPeriodAttr);
AttrPutS('Sep',sControlDimension,'Oct',sPrevPeriodAttr);
AttrPutS('October',sControlDimension,'Oct',sLongNameAttr);

AttrPutS('Dec',sControlDimension,'Nov',sNextPeriodAttr);
AttrPutS('Oct',sControlDimension,'Nov',sPrevPeriodAttr);
AttrPutS('November',sControlDimension,'Nov',sLongNameAttr);

AttrPutS('Jan',sControlDimension,'Dec',sNextPeriodAttr);
AttrPutS('Nov',sControlDimension,'Dec',sPrevPeriodAttr);
AttrPutS('December',sControlDimension,'Dec',sLongNameAttr);

AttrPutS('Feb',sControlDimension,'Jan1',sNextPeriodAttr);
AttrPutS('Dec',sControlDimension,'Jan1','Previous Period');
AttrPutS('January',sControlDimension,'Jan1',sLongNameAttr);

AttrPutS('Mar',sControlDimension,'Feb1','Next Period');
AttrPutS('Jan',sControlDimension,'Feb1','Previous Period');
AttrPutS('February',sControlDimension,'Feb1',sLongNameAttr);

AttrPutS('Apr',sControlDimension,'Mar1','Next Period');
AttrPutS('Feb',sControlDimension,'Mar1','Previous Period');
AttrPutS('March',sControlDimension,'Mar1',sLongNameAttr);

AttrPutS('May',sControlDimension,'Apr1','Next Period');
AttrPutS('Mar',sControlDimension,'Apr1','Previous Period');
AttrPutS('April',sControlDimension,'Apr1',sLongNameAttr);

AttrPutS('Jun',sControlDimension,'May1','Next Period');
AttrPutS('Apr',sControlDimension,'May1','Previous Period');
AttrPutS('May',sControlDimension,'May1',sLongNameAttr);

AttrPutS('Jul',sControlDimension,'Jun1','Next Period');
AttrPutS('May',sControlDimension,'Jun1','Previous Period');
AttrPutS('June',sControlDimension,'Jun1',sLongNameAttr);

AttrPutS('Aug',sControlDimension,'Jul1','Next Period');
AttrPutS('Jun',sControlDimension,'Jul1','Previous Period');
AttrPutS('July',sControlDimension,'Jul1',sLongNameAttr);

AttrPutS('Sep',sControlDimension,'Aug1','Next Period');
AttrPutS('Jul',sControlDimension,'Aug1','Previous Period');
AttrPutS('August',sControlDimension,'Aug1',sLongNameAttr);

AttrPutS('Oct',sControlDimension,'Sep1','Next Period');
AttrPutS('Aug',sControlDimension,'Sep1','Previous Period');
AttrPutS('September',sControlDimension,'Sep1',sLongNameAttr);

AttrPutS('Nov',sControlDimension,'Oct1','Next Period');
AttrPutS('Sep',sControlDimension,'Oct1','Previous Period');
AttrPutS('October',sControlDimension,'Oct1',sLongNameAttr);

AttrPutS('Dec',sControlDimension,'Nov1','Next Period');
AttrPutS('Oct',sControlDimension,'Nov1','Previous Period');
AttrPutS('November',sControlDimension,'Nov1',sLongNameAttr);

AttrPutS('Jan',sControlDimension,'Dec1','Next Period');
AttrPutS('Nov',sControlDimension,'Dec1','Previous Period');
AttrPutS('December',sControlDimension,'Dec1',sLongNameAttr);

#########################################################
## Insert Elements NB: Does not matter if elements  exist
#########################################################

nMinYear = nStartYear;
nMaxYear = nEndYear;

# Loop number of Years

WHILE(nMinYear <= nMaxYear);
	sMinYear = NumberToString(nMinYear);
	# Number of Months - include Op Bal (0) and P13
	nMinMonth = 0;
	nMaxMonth = 13;

	# Add FY Consolidation
	sYearFY = 'FY '|sMinYear;
	DimensionElementInsert(cDimName,'',sYearFY,'C');
	DimensionElementComponentAdd(cDimName,sFYConsol,sYearFY,1);
	# Add Quarter Consolidation
	sYearQtr = 'FY '|sMinYear|'-QTR ' ;
	DimensionElementInsert(cDimName,'',sYearQTR,'C');
	DimensionElementComponentAdd(cDimName,sQTRConsol,sYearQTR,1);
	# Add YTD Consolidation
	sYearYTD = 'FY '|sMinYear |'-YTD';
	DimensionElementInsert(cDimName,'',sYearYTD,'C');
	DimensionElementComponentAdd(cDimName,sYTDConsol,sYearYTD,1);
	# Add YTG Consolidation
	sYearYTG = 'FY '|sMinYear |'-YTG';
	DimensionElementInsert(cDimName,'',sYearYTG,'C');
	DimensionElementComponentAdd(cDimName,sYTGConsol, sYearYTG,1);
	# Add LTD Consolidation
	sYearLTD = 'FY '|sMinYear |'-LTD';
	DimensionElementInsert(cDimName,'',sYearLTD,'C');
	DimensionElementComponentAdd(cDimName,sLTDConsol,sYearLTD,1);
	# Add a Driver element
	IF(pIncludeDriverElement@='Y');
		sYearDriver = sMinYear |'-Driver';
		DimensionElementInsert(cDimName,'',sYearDriver,'N');
		DimensionElementComponentAdd(cDimName,sDriverConsol,sYearDriver,1);
	ENDIF;

	# Add an Input Element for each year
	IF(pIncludeInputElement@='Y');
		sYearInput = sMinYear |'-Input';
		DimensionElementInsert(cDimName,'',sYearInput,'N');
		DimensionElementComponentAdd(cDimName,sInputConsol,sYearInput,1);
	ENDIF;

	#QTR Consolidations# - don't bother with P13
	# Loop through 4 times to add each Quarter Consolidation within each year
	nQTRMin = 1;
	nQTRMax = 4;
  
	WHILE(nQTRMin <= nQTRMax);
		sQElement = 'FY '|sMinYear | '-Q' | NumberToString(nQTRMin);
		DimensionElementInsert(cDimName,'',sQElement,'C');
		DimensionElementComponentAdd(cDimName,sYearQTR,sQElement,1);
		nQTRMin = nQTRMin +1;
	END;


	#YTD Consolidations - Include P13
	nYTDMin = 1;
	nYTDMax = 13;
	WHILE(nYTDMin <= nYTDMax);
		IF(nYTDMin <10);
			sYTDElement = 'FY '|sMinYear | '-0' | NumberToString(nYTDMin) | '-YTD';
		ELSE;
			sYTDElement = 'FY '|sMinYear | '-' | NumberToString(nYTDMin) | '-YTD';
		ENDIF;
		DimensionElementInsert(cDimName,'',sYTDElement,'C');
		DimensionElementComponentAdd(cDimName,sYearYTD,sYTDElement,1);
	nYTDMin = nYTDMin +1;
	END;

	#YTG Consolidations 
	nYTGMin = 1;
	nYTGMax = 11;
	WHILE(nYTGMin <= nYTGMax);
		IF(nYTGMin <10);
			sYTGElement = 'FY '|sMinYear | '-0' | NumberToString(nYTGMin) | '-YTG';
		ELSE;
			sYTGElement = 'FY '|sMinYear | '-' | NumberToString(nYTGMin) | '-YTG';
		ENDIF;
		DimensionElementInsert(cDimName,'',sYTGElement,'C');
		DimensionElementComponentAdd(cDimName,sYearYTG,sYTGElement,1);
		nYTGMin = nYTGMin +1;
	END;

	#LTD Consolidations - Include a P13
	nLTDMin = 1;
	nLTDMax = 13;
	WHILE(nLTDMin <= nLTDMax);
		IF(nLTDMin <10);
			sLTDElement = 'FY '|sMinYear | '-0' | NumberToString(nLTDMin) | '-LTD';
		ELSE;
			sLTDElement = 'FY '|sMinYear | '-' | NumberToString(nLTDMin) | '-LTD';
		ENDIF;
		DimensionElementInsert(cDimName,'',sLTDElement,'C');
		DimensionElementComponentAdd(cDimName,sYearLTD,sLTDElement,1);
	nLTDMin = nLTDMin +1;
	END;

	#N level Month elements 00 - 13-----------------------------------------------------------------
	#N Level Element Insert and Assign to Consolidations
	WHILE(nMinMonth <= nMaxMonth);
		sMinMonth = NumberToString(nMinMonth);
		IF(nMinMonth <10);
			sElement = sMinYear | '-0' | sMinMonth;	
		ELSE;
			sElement = sMinYear | '-' | sMinMonth;	
		ENDIF;
		DimensionElementInsert(cDimName,'',sElement,'N');

		#FY Consolidations - don't bother with P13
		# Add the n level elements 1 - 12 under Year's "FY YYYY" consolidation
		IF((nMinMonth >=1) & (nMinMonth <=12));
			DimensionElementComponentAdd(cDimName, 'FY '|sMinYear ,sElement,1);
		ENDIF;

		#QTR Consolidations# - exclude P13
		IF((nMinMonth >=1) & (nMinMonth <=3));
			DimensionElementComponentAdd(cDimName,'FY '|sMinYear | '-Q1',sElement,1);
		ELSEIF((nMinMonth >=4) & (nMinMonth <=6));
			DimensionElementComponentAdd(cDimName,'FY '|sMinYear | '-Q2',sElement,1);
		ELSEIF((nMinMonth >=7) & (nMinMonth <=9));
			DimensionElementComponentAdd(cDimName,'FY '|sMinYear | '-Q3',sElement,1);
		ElSEIF((nMinMonth >=10) & (nMinMonth <=12));
			DimensionElementComponentAdd(cDimName,'FY '|sMinYear | '-Q4',sElement,1);			
		ENDIF;

		#YTD Consolidations# - include P13
		nYTDMin = 1;
		nYTDMax = 13;
		WHILE(nYTDMin <= nYTDMax);		
			IF(nMinMonth <= nYTDMin);
			IF(nMinMonth >= 1);
			IF(nYTDMin < 10);
				sParent = 'FY '|sMinYear | '-0' | NumberToString(nYTDMin) | '-YTD';
			ELSE;
				sParent = 'FY '|sMinYear | '-' | NumberToString(nYTDMin) | '-YTD';
			ENDIF;
				DimensionElementComponentAdd(cDimName,sParent,sElement,1);
			ENDIF;
			ENDIF;
		nYTDMin = nYTDMin + 1; 
		END;

	#YTG Consolidations - exclude P13
	nYTGMin = 1;
	nYTGMax = 11;
	WHILE(nYTGMin <= nYTGMax);
		IF(nMinMonth > nYTGMin);
		IF(nYTGMin < 10);
			sParent = 'FY '|sMinYear | '-0' | NumberToString(nYTGMin) | '-YTG';
		ELSE;
			sParent = 'FY '|sMinYear | '-' | NumberToString(nYTGMin) | '-YTG';
		ENDIF;
			DimensionElementComponentAdd(cDimName,sParent,sElement,1);
		ENDIF;
	nYTGMin = nYTGMin+1; 
	END;

	#LTD Consolidations - Include P13
	nLTDMin = 1;
	nLTDMax = 13;
	WHILE(nLTDMin <= nLTDMax);		
		IF(nMinMonth <= nLTDMin);
		IF(nLTDMin < 10);
			sParent = 'FY '|sMinYear | '-0' | NumberToString(nLTDMin) | '-LTD';
		ELSE;
			sParent = 'FY '|sMinYear | '-' | NumberToString(nLTDMin) | '-LTD';
		ENDIF;
		DimensionElementComponentAdd(cDimName,sParent,sElement,1);
		ENDIF;
	nLTDMin = nLTDMin+1; 
	END;

	nMinMonth = nMinMonth +1;
	END;

nMinYear = nMinYear+1;
END;

DimensionSortOrder(cDimName, 'ByInput', 'Ascending', 'ByHierarchy' , 'Ascending');
573,3

#****Begin: Generated Statements***
#****End: Generated Statements****
574,3

#****Begin: Generated Statements***
#****End: Generated Statements****
575,441

#****Begin: Generated Statements***
#****End: Generated Statements****

IF(1=1);

#########################################################
## Add Attributes
#########################################################
nMinYear = nStartYear;
nMaxYear = nENDYear;

## Loop Years
WHILE(nMinYear <= nMaxYear);
	nMinMonth = 0;
	nMaxMonth = 13;
	sMinYear = NumberToString(nMinYear);
 
	#--Fiscal Year (FY)
	sYearFY = 'FY '|sMinYear;
	# Insert firstperiod / lastperiod 
	sAttrValue =  sMinYear | '-01'; AttrPutS(sAttrValue, cDimName, sYearFY,sFirstPeriodAttr);
	sAttrValue =  sMinYear | '-12'; AttrPutS(sAttrValue, cDimName, sYearFY,sLastPeriodAttr);
	# Insert previousyear / nextyear 
	sAttrValue =  NumberToString(nMinYear -1); AttrPutS(sAttrValue, cDimName, sYearFY,sPrevYearAttr);
	sAttrValue =  NumberToString(nMinYear +1); AttrPutS(sAttrValue, cDimName, sYearFY,sNextYearAttr);
	# Insert Caption
	sAttrValue =  NumberToString(nMinYear); AttrPutS(sAttrValue, cDimName, sYearFY,sCaptionAttr);
	# Insert Year Name 
	sAttrValue = sMinYear ; AttrPutS(sAttrValue, cDimName, sYearFY, sYearNameAttr) ;
  
	#--YTD
	sYearYTD = 'FY '|sMinYear |'-YTD';
	# Insert firstperiod / lastperiod 
	sAttrValue =  sMinYear | '-01'; AttrPutS(sAttrValue, cDimName, sYearYTD,sFirstPeriodAttr);
	sAttrValue =  sMinYear | '-13'; AttrPutS(sAttrValue, cDimName, sYearYTD,sLastPeriodAttr);
	# Insert previousyear / nextyear 
	sAttrValue =  NumberToString(nMinYear -1); AttrPutS(sAttrValue, cDimName, sYearYTD,sPrevYearAttr);
	sAttrValue =  NumberToString(nMinYear +1);AttrPutS(sAttrValue, cDimName, sYearYTD,sNextYearAttr);
	# Insert Caption
	sAttrValue =  NumberToString(nMinYear)|'-YTD'; AttrPutS(sAttrValue, cDimName, sYearYTD,sCaptionAttr);
	# Insert  Year Name 
	  sAttrValue = sMinYear ; AttrPutS(sAttrValue, cDimName, sYearYTD, sYearNameAttr) ;


	#--YTG
	sYearYTG = 'FY '|sMinYear |'-YTG';
	# Insert firstperiod / lastperiod 
	sAttrValue =  sMinYear | '-01'; AttrPutS(sAttrValue, cDimName, sYearYTG,sFirstPeriodAttr);
	sAttrValue =  sMinYear | '-13'; AttrPutS(sAttrValue, cDimName, sYearYTG,sLastPeriodAttr);
	# Insert previousyear / nextyear 
	sAttrValue =  NumberToString(nMinYear -1); AttrPutS(sAttrValue, cDimName, sYearYTG,sPrevYearAttr);
	sAttrValue =  NumberToString(nMinYear +1); AttrPutS(sAttrValue, cDimName, sYearYTG,sNextYearAttr);
	# Insert Caption
	sAttrValue =  NumberToString(nMinYear)|'-YTG'; AttrPutS(sAttrValue, cDimName, sYearYTG,sCaptionAttr);
	# Insert  Year Name 
	sAttrValue = sMinYear ; AttrPutS(sAttrValue, cDimName, sYearYTG, sYearNameAttr) ;

	#--LTD
	sYearLTD = 'FY '|sMinYear |'-LTD';
	# Insert firstperiod / lastperiod
	sAttrValue =  sMinYear | '-00'; AttrPutS(sAttrValue, cDimName, sYearLTD,sFirstPeriodAttr);
	sAttrValue =  sMinYear | '-13'; AttrPutS(sAttrValue, cDimName, sYearLTD,sLastPeriodAttr);
	# Insert previousyear / nextyear 
	sAttrValue =  NumberToString(nMinYear -1); AttrPutS(sAttrValue, cDimName, sYearLTD,sPrevYearAttr);
	sAttrValue =  NumberToString(nMinYear +1); AttrPutS(sAttrValue, cDimName, sYearLTD,sNextYearAttr);
	# Insert Caption
	sAttrValue =  NumberToString(nMinYear)|'-LTD'; AttrPutS(sAttrValue, cDimName, sYearLTD,sCaptionAttr);
	# Insert  Year Name 
	sAttrValue = sMinYear ; AttrPutS(sAttrValue, cDimName, sYearLTD, sYearNameAttr) ;
	
    #--QTR
	sYearQTR = 'FY '|sMinYear |'-QTR';

	# Insert firstperiod / lastperiod
	sAttrValue =  sMinYear | '-01'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q1',sFirstPeriodAttr);
	sAttrValue =  sMinYear | '-03'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q1',sLastPeriodAttr);
	sAttrValue =  sMinYear | '-04'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q2',sFirstPeriodAttr);
	sAttrValue =  sMinYear | '-06'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q2',sLastPeriodAttr);
	sAttrValue =  sMinYear | '-07'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q3',sFirstPeriodAttr);
	sAttrValue =  sMinYear | '-09'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q3',sLastPeriodAttr);
	sAttrValue =  sMinYear | '-10'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q4',sFirstPeriodAttr);
	sAttrValue =  sMinYear | '-13'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q4',sLastPeriodAttr);

	# Insert Caption
	sAttrValue =  NumberToString(nMinYear)|'-QTR'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-QTR',sCaptionAttr); 
	sAttrValue =  NumberToString(nMinYear)|'-Q1'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q1',sCaptionAttr);
	sAttrValue =  NumberToString(nMinYear)|'-Q2'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q2',sCaptionAttr);
	sAttrValue =  NumberToString(nMinYear)|'-Q3'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q3',sCaptionAttr);
	sAttrValue =  NumberToString(nMinYear)|'-Q4'; AttrPutS(sAttrValue, cDimName, 'FY '|sMinYear |'-Q4',sCaptionAttr); 

	# N Level Element ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
	WHILE(nMinMonth <= nMaxMonth);
    
		sMinMonth = NumberToString(nMinMonth);
		IF(nMinMonth <10); sElement = sMinYear | '-0' | sMinMonth; ELSE; sElement = sMinYear | '-' | sMinMonth; ENDIF;

		#Month 
		sAttrValue = 'FY '|NumberToString(nMinYear); AttrPutS(sAttrValue, cDimName, sElement,sFinYearAttr);
		#FinYear 
		sAttrValue = 'FY '|NumberToString(nMinYear); AttrPutS(sAttrValue, cDimName, sElement,sFinYearAttr);
		# NextYear 
		sAttrValue = NumberToString(nMinYear +1); AttrPutS(sAttrValue, cDimName, sElement,sNextYearAttr);
		# PreviousYear 
		sAttrValue = NumberToString(nMinYear -1); AttrPutS(sAttrValue, cDimName, sElement,sPrevYearAttr);
		# NextMonth
		IF(nMinMonth = 0);
		ELSEIF(nMinMonth = 12);
			sNextElement = NumberToString(nMinYear+1) | '-01';	
			AttrPutS(sNextElement, cDimName, sElement,sNextPeriodAttr);
		ELSE;
			nNextElement = nMinMonth+1;
			IF(nNextElement <10);
				sNextElement = sMinYear | '-0' | NumberToString(nNextElement);	
			ELSE;
				sNextElement = sMinYear | '-' | NumberToString(nNextElement);	
			ENDIF;
			AttrPutS(sNextElement, cDimName, sElement,sNextPeriodAttr);
		ENDIF;
		
		# Previous Month
		IF(nMinMonth = 0);
		
		ELSEIF(nMinMonth = 1);
			sPreviousElement = NumberToString(nMinYear-1) | '-12';	
			AttrPutS(sPreviousElement, cDimName, sElement,sPrevPeriodAttr);
		ELSE;
			nPreviousElement = nMinMonth-1;
			IF(nPreviousElement <10);
				sPreviousElement = sMinYear | '-0' | NumberToString(nPreviousElement);	
			ELSE;
				sPreviousElement = sMinYear | '-' | NumberToString(nPreviousElement);	
			ENDIF;
		AttrPutS(sPreviousElement, cDimName, sElement,sPrevPeriodAttr);
		ENDIF;

		# Alias - Captions and Long Name
		IF(nMinMonth = 0);
			nOpYear = nMinYear - 1;
			sLookupMonth = 'OB-' | SUBST(NumberToString(nOpYear),3,2);
			AttrPutS(sLookupMonth, cDimName, sElement,sCaptionAttr);
			sLongName = 'Opening Balance ' | NumberToString(nOpYear);
			AttrPutS(sLongName, cDimName, sElement,sLongNameAttr);	
			#No OO consolidation

			# Period 13 Aliases
		ELSEIF(nMinMonth = 13);
			sLookupMonth = 'P13-' | SUBST(NumberToString(nMinYear),3,2);
			AttrPutS(sLookupMonth, cDimName, sElement,sCaptionAttr);
			sLongName = 'Period 13 ' | NumberToString(nMinYear);
			AttrPutS(sLongName, cDimName, sElement,sLongNameAttr);	

			#Also add alias to parent(s)
			sSuffix = ' YTD';
			sParentAlias = sLookupMonth |  sSuffix;
			sParentAliasElement = 'FY '| sElement | '-YTD';
			sLongNameConsol = sLongName | sSuffix;
			AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
			AttrPutS(sLongNameConsol, cDimName, sParentAliasElement,sLongNameAttr);	

			sSuffix = ' LTD';
			sParentAlias = sLookupMonth |  sSuffix;
			sParentAliasElement =  'FY '|sElement | '-LTD';
			sLongNameConsol = sLongName | sSuffix;
			AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);	
			AttrPutS(sLongNameConsol, cDimName, sParentAliasElement,sLongNameAttr);	

		ELSEIF(nMinMonth=1);
			IF(sStartMonth @<>'Jan');
				s_LongName = AttrS(sControlDimension, sStartMonth, sLongNameAttr);	
				s_Year = NumberToString(nMinYear-1);
				sLookupMonth = sStartMonth | '-' | SUBST(s_Year,3,2);
				AttrPutS(sLookupMonth, cDimName, sElement,sCaptionAttr);
				AttrPutS(SUBST(sLookupMonth,1,3), cDimName, sElement,sMonthAttr);
				sLongNameYear = s_LongName |' '|s_Year;
				AttrPutS(sLongNameYear, cDimName, sElement,sLongNameAttr);

				#Also add alias to parent(s)
				sSuffix = ' YTD';
				sParentAlias = sLookupMonth |  sSuffix;
				sParentAliasElement =  'FY '|sElement | '-YTD';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);	

				sSuffix = ' YTG';	
				sParentAlias = sLookupMonth |  sSuffix;
				sParentAliasElement =  'FY '|sElement | '-YTG';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);	

				sSuffix = ' LTD';
				sParentAlias = sLookupMonth |  sSuffix;
				sParentAliasElement =  'FY '|sElement | '-LTD';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);	
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);	
			ELSE;
				s_LongName = AttrS(sControlDimension, sStartMonth, sLongNameAttr);	
				s_Year = NumberToString(nMinYear);
				sLookupMonth = sStartMonth | ' ' | SUBST(s_Year,3,2);
				AttrPutS(SUBST(sLookupMonth,1,3), cDimName, sElement,sMonthAttr);
				AttrPutS(sLookupMonth, cDimName, sElement,sCaptionAttr);
				sLongNameYear = s_LongName |' '|s_Year;
				AttrPutS(sLongNameYear, cDimName, sElement,sLongNameAttr);

				#Also add alias to parent(s)
				sSuffix = ' YTD';
				sParentAlias = sLookupMonth |  sSuffix;
				sParentAliasElement =  'FY '|sElement | '-YTD';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);	

				sSuffix = ' YTG';
				sParentAlias = sLookupMonth |  sSuffix;
				sParentAliasElement =  'FY '|sElement | '-YTG';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);

				sSuffix = ' LTD';
				sParentAlias = sLookupMonth |  sSuffix;
				sParentAliasElement =  'FY '|sElement | '-LTD';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);		
			ENDIF;

		ELSE;
			IF(sStartMonth @<>'Jan');
				sLookupMonth = SUBST(DimNM(sControlDimension,DimIx(sControlDimension,sStartMonth)+nMinMonth-1),1,3);
				s_LongName = AttrS(sControlDimension, sLookupMonth, sLongNameAttr);	
				IF(DimIx(sControlDimension,sStartMonth)+nMinMonth-1>12);
					s_Year = NumberToString(nMinYear);
					sLookupMonthYear = sLookupMonth | '-' | SUBST(s_Year ,3,2);
				ELSE;
					s_Year = NumberToString(nMinYear-1);
					sLookupMonthYear = sLookupMonth | '-' | SUBST(s_Year,3,2);
				ENDIF;
				sLongNameYear = s_LongName |' '|s_Year;
				AttrPutS(sLookupMonthYear, cDimName, sElement,sCaptionAttr);
				AttrPutS(SUBST(sLookupMonthYear,1,3), cDimName, sElement,sMonthAttr);
				AttrPutS(sLongNameYear, cDimName, sElement,sLongNameAttr);

				## Also add alias to parent(s)
				# YTD Captions
				sSuffix = ' YTD';
				sParentAlias = sLookupMonthYear | sSuffix;
				sParentAliasElement = 'FY '| sElement | '-YTD';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);

				# YTG Caption Attributes
				#No YTG for month12
				IF(nMinMonth <= 11);	
					sSuffix = ' YTG';
					sParentAlias = sLookupMonthYear | sSuffix;
					sParentAliasElement =  'FY '|sElement | '-YTG';
					sLongName = sLongNameYear | sSuffix;
					AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
					AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);
				ENDIF;
				sSuffix = ' LTD';
				sParentAlias = sLookupMonthYear | sSuffix;
				sParentAliasElement =  'FY '|sElement | '-LTD';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);
			ELSE;
				s_Year = NumberToString(nMinYear);
				sLookupMonth = SUBST(DimNM(sControlDimension,DimIx(sControlDimension,sStartMonth)+nMinMonth-1),1,3);		
				sLookupMonthYear = sLookupMonth | '-' | SUBST(s_Year,3,2);
				s_LongName = AttrS(sControlDimension, sLookupMonth, sLongNameAttr);	
				sLongNameYear = s_LongName |' '|s_Year;
				AttrPutS(sLongNameYear, cDimName, sElement,sLongNameAttr);
				AttrPutS(sLookupMonthYear, cDimName, sElement,sCaptionAttr);
				AttrPutS(SUBST(sLookupMonthYear,1,3), cDimName, sElement,sMonthAttr);

				# Also add alias to parent(s)
				sSuffix = ' YTD';
				sParentAlias = sLookupMonthYear | sSuffix;
				sParentAliasElement =  'FY '|sElement | '-YTD';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);

				sSuffix = ' YTG';
				sParentAlias = sLookupMonthYear | sSuffix;
				sParentAliasElement =  'FY '|sElement | '-YTG';
				sLongName = sLongNameYear | sSuffix;
				#AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				#AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);
	
				sSuffix = ' LTD';
				sParentAlias = sLookupMonthYear | sSuffix;
				sParentAliasElement =  'FY '|sElement | '-LTD';
				sLongName = sLongNameYear | sSuffix;
				AttrPutS(sParentAlias, cDimName, sParentAliasElement,sCaptionAttr);
				AttrPutS(sLongName, cDimName, sParentAliasElement,sLongNameAttr);

			ENDIF;

		ENDIF;
	
	#--Quarter Attributes
	n_LoopCtrl = 1;
	n_LoopMax = 4;
	WHILE(n_LoopCtrl <= n_LoopMax);
		sQ = NumberToString(n_LoopCtrl);
		sLongName = 'Quarter '|sQ|' '|sMinYear;
		sCaption =  'Q'|sQ|' '|sMinYear;
		sElement = 'FY '|sMinYear|'-Q'|sQ;
		sPriorYrValue =  NumberToString(nMinYear -1);
		sNextYrValue =  NumberToString(nMinYear +1);
		nComponents = ElCompN(cDimName,sElement);
		sFirstAttr = ElComp(cDimName, sElement, 1);
		sLastAttr = ElComp(cDimName, sElement, nComponents);

		## Insert Attributes
		# Insert First and Last Period Attributes
		AttrPutS(sFirstAttr, cDimName, sElement,sFirstPeriodAttr);
		AttrPutS(sLastAttr, cDimName, sElement,sLastPeriodAttr);

		#Insert previousyear / nextyear attributes
		AttrPutS(sPriorYrValue, cDimName, sElement,sPrevYearAttr);
		AttrPutS(sNextYrValue, cDimName,sElement,sNextYearAttr);

		# Insert Quarter Captions and Long Name
		AttrPutS(sLongName, cDimName, sElement,sLongNameAttr);
		AttrPutS( sCaption, cDimName, sElement,sCaptionAttr);

		n_LoopCtrl = n_LoopCtrl + 1;
	END;
    

	#YTD Consolidations
	nYTDMin = 1;
	nYTDMax = 13;
	WHILE(nYTDMin <= nYTDMax);		
		IF(nMinMonth <= nYTDMin);
		IF(nMinMonth = 0);
          #
		ELSE;
		IF(nYTDMin < 10);
			sParent = 'FY '|sMinYear | '-0' | NumberToString(nYTDMin) | '-YTD';
		ELSE;
			sParent = 'FY '|sMinYear | '-' | NumberToString(nYTDMin) | '-YTD';
		ENDIF;
			
		#Insert firstperiod and lastperiod attribute
		nComponents = ElCompN(cDimName,sParent);
		sFirstAttr = ElComp(cDimName, sParent, 1);
		sLastAttr = ElComp(cDimName, sParent, nComponents);
		AttrPutS(sFirstAttr, cDimName, sParent,sFirstPeriodAttr);
		AttrPutS(sLastAttr, cDimName, sParent,sLastPeriodAttr);
		#Insert previousyear / nextyear attributes
		sAttrValue =  NumberToString(nMinYear -1);
		AttrPutS(sAttrValue, cDimName, sParent,sPrevYearAttr);
		sAttrValue =  NumberToString(nMinYear +1);
		AttrPutS(sAttrValue, cDimName,sParent,sNextYearAttr);

		ENDIF;
		ENDIF;
		nYTDMin = nYTDMin+1; 
	END;

	#YTG Consolidations
	nYTGMin = 1;
	nYTGMax = 11;
	WHILE(nYTGMin <= nYTGMax);		

		IF(nMinMonth > nYTGMin);
		IF(nYTGMin < 10);
			sParent = 'FY '|sMinYear | '-0' | NumberToString(nYTGMin) | '-YTG';
		ELSE;
			sParent = 'FY '|sMinYear | '-' | NumberToString(nYTGMin) | '-YTG';
		ENDIF;

		#Insert firstperiod and lastperiod attribute
		nComponents = ElCompN(cDimName,sParent);
		sFirstAttr = ElComp(cDimName, sParent, 1);
		sLastAttr = ElComp(cDimName, sParent, nComponents);
		AttrPutS(sFirstAttr, cDimName, sParent,sFirstPeriodAttr);
		AttrPutS(sLastAttr, cDimName, sParent,sLastPeriodAttr);
		#Insert previousyear / nextyear attributes
		sAttrValue =  NumberToString(nMinYear -1);
		AttrPutS(sAttrValue, cDimName, sParent,sPrevYearAttr);
		sAttrValue =  NumberToString(nMinYear +1);
		AttrPutS(sAttrValue, cDimName,sParent,sNextYearAttr);
		ENDIF;
		nYTGMin = nYTGMin+1; 
	END;

	#LTD Consolidations
	nLTDMin = 1;
	nLTDMax = 13;
	WHILE(nLTDMin <= nLTDMax);		
		IF(nMinMonth <= nLTDMin);
		IF(nLTDMin < 10);
			sParent = 'FY '|sMinYear | '-0' | NumberToString(nLTDMin) | '-LTD';
		ELSE;
			sParent = 'FY '|sMinYear | '-' | NumberToString(nLTDMin) | '-LTD';
		ENDIF;
        
		#Insert firstperiod and lastperiod attribute
		nComponents = ElCompN(cDimName,sParent);
		sFirstAttr = ElComp(cDimName, sParent, 1);
		sLastAttr = ElComp(cDimName, sParent, nComponents);
		AttrPutS(sFirstAttr, cDimName, sParent,sFirstPeriodAttr);
		AttrPutS(sLastAttr, cDimName, sParent,sLastPeriodAttr);
		#Insert previousyear / nextyear attributes
		sAttrValue =  NumberToString(nMinYear -1);
		AttrPutS(sAttrValue, cDimName, sParent,sPrevYearAttr);
		sAttrValue =  NumberToString(nMinYear +1);
		AttrPutS(sAttrValue, cDimName,sParent,sNextYearAttr);

		ENDIF;
		nLTDMin = nLTDMin+1; 
	END;

	nMinMonth = nMinMonth +1;
	END;

	# Add FY Long Name
	sElement = NumberToString(nMinYear);
	sLongName = sElement | ' FY';
	AttrPutS(sLongName, cDimName, sElement,sLongNameAttr);

	nMinYear = nMinYear+1;
END;


#Clean up System Objects
#DimensionDestroy(sControlDimension);
# Restore cube logging for bulk data loads - performance improvements
CubeSetLogChanges(cCube, cCubeLogging);

ENDIF;
576,CubeAction=1511DataAction=1503CubeLogChanges=0
930,0
638,1
804,0
1217,0
900,
901,
902,
938,0
937,
936,
935,
934,
932,0
933,0
903,
906,
929,
907,
908,
904,0
905,0
909,0
911,
912,
913,
914,
915,
916,
917,0
918,1
919,0
920,50000
921,""
922,""
923,0
924,""
925,""
926,""
927,""
