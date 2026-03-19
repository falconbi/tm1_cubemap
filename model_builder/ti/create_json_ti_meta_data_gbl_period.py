"""
create_json_ti_gbl_period.py
==============================
Generates ti_gbl_period.json — the TI process that builds the
GBL Period dimension in TM1.

Run this script to regenerate the JSON whenever the TI logic needs
to change. The output is written to ti_gbl_period.json in the
same directory, ready to be deployed by create_ti_meta_data_gbl_period.py.

Usage:
    python create_json_ti_gbl_period.py

Output:
    ti_gbl_period.json  (in same directory as this script)

The JSON produced is identical in structure and content to the
original — the only default value changed is pPeriodDimName,
which is set to 'GBL Period' instead of 'Period'.
"""

import json
import os

PROCESS_NAME = 'META DATA GBL Period'
JSON_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_files')
os.makedirs(JSON_DIR, exist_ok=True)
OUTPUT_FILE  = os.path.join(JSON_DIR, 'ti_meta_data_gbl_period.json')


# ══════════════════════════════════════════════════════════════════════════════
# TI Code Sections
# Each section is a raw string preserving exact whitespace and line endings.
# ══════════════════════════════════════════════════════════════════════════════

PROLOG = r"""
#****Begin: Generated Statements***
#****End: Generated Statements****

#########################################################
## META DATA GBL Period
## Builds the Period dimension with FY, QTR, YTD, YTG,
## LTD hierarchies. Supports any fiscal year start month.
## Includes leap year detection and Days in Period attribute.
##
## Parameters:
##   pStartYear        - First fiscal year to create e.g. 2014
##   pEndYear          - Last fiscal year to create  e.g. 2040
##   pStartMonth       - First month of fiscal year  e.g. Jul
##   pPeriodDimName    - Target dimension name        e.g. Period
##   pDeleteAndRebuild - Wipe and rebuild if Y
##   pIncludeDriverElement - Add YYYY-Driver N element per year
##   pIncludeInputElement  - Add YYYY-Input N element per year
##   pDebug            - Write progress to error log if Y
#########################################################

#########################################################
## Constants
#########################################################
cDimName        = pPeriodDimName;
cProcessName    = GetProcessName();
cTimestamp      = TimSt( Now, '\Y\m\d\h\i\s' );
cErrorDirectory = GetProcessErrorFileDirectory;

#########################################################
## Consolidation Name Constants
#########################################################
sTopConsol  = cDimName | ' Consolidations';
sRepConsol  = 'Reporting';
sSysConsol  = 'System';

sFYConsol   = 'All FY';
sQTRConsol  = 'All QTR';
sYTDConsol  = 'All YTD';
sYTGConsol  = 'All YTG';
sLTDConsol  = 'All LTD';

# Initialise optional consolidation names to empty string
# to avoid undefined variable errors in unwind block
sDriverConsol = '';
sInputConsol  = '';

IF( pIncludeDriverElement @= 'Y' );
    sDriverConsol = 'All Driver';
ENDIF;
IF( pIncludeInputElement @= 'Y' );
    sInputConsol = 'All Input';
ENDIF;

sNoElement = 'No ' | cDimName;

#########################################################
## Attribute Name Constants
#########################################################
sCaptionAttr      = 'Caption';
sLongNameAttr     = 'Long Name';
sNextPeriodAttr   = 'Next Period';
sPrevPeriodAttr   = 'Previous Period';
sNextYearAttr     = 'Next Year';
sPrevYearAttr     = 'Previous Year';
sLastPeriodAttr   = 'Last Period';
sFirstPeriodAttr  = 'First Period';
sMonthActualsAttr = 'Month Contains Actuals';
sYearNameAttr     = 'Year Name';
sFinYearAttr      = 'Fin Year';
sMonthAttr        = 'Month';
sDaysInPeriodAttr = 'Days in Period';
sLeapYearAttr     = 'Leap Year';
sCalMonthNumAttr  = 'Calendar Month Number';
sCalYearAttr      = 'Calendar Year';
sStartSerialAttr  = 'Period Start Serial';
sEndSerialAttr    = 'Period End Serial';

#########################################################
## Parameter Capture
#########################################################
sStartYear  = pStartYear;
sEndYear    = pEndYear;
sStartMonth = pStartMonth;
nStartYear  = StringToNumber( sStartYear );
nEndYear    = StringToNumber( sEndYear );

#########################################################
## Parameter Validation
#########################################################
nBreakFlag = 0;

IF( Long( sStartYear ) <> 4 );
    nBreakFlag = 1;
    ItemReject( 'pStartYear must be in YYYY format e.g. 2014' );
ENDIF;

IF( Long( sEndYear ) <> 4 );
    nBreakFlag = 1;
    ItemReject( 'pEndYear must be in YYYY format e.g. 2040' );
ENDIF;

IF( Long( sStartMonth ) <> 3 );
    nBreakFlag = 1;
    ItemReject( 'pStartMonth must be 3-character month e.g. Jul' );
ENDIF;

IF( nStartYear >= nEndYear );
    nBreakFlag = 1;
    ItemReject( 'pStartYear must be less than pEndYear' );
ENDIF;

IF( nBreakFlag = 1 );
    ProcessError;
ENDIF;

#########################################################
## Create Dimension If Not Exists
#########################################################
IF( DimensionExists( cDimName ) = 0 );
    DimensionCreate( cDimName );
ENDIF;

IF( pDeleteAndRebuild @= 'Y' );
    DimensionDeleteAllElements( cDimName );
ENDIF;

#########################################################
#########################################################
## Unravel Existing Consolidations (Native TM1)
## Removes all children from each top-level consolidation
## before rebuilding. Safe on empty or populated dimensions.
#########################################################

IF( DimSiz( cDimName ) > 0 );

    # Helper subprocedure inline - loop components and delete
    # We unwind by deleting and re-inserting each C element empty

    nEleCount = DimSiz( cDimName );
    nEleIdx = 1;
    WHILE( nEleIdx <= nEleCount );
        sEle = DimNm( cDimName, nEleIdx );
        IF( ElCompN( cDimName, sEle ) > 0 );
            nComp = ElCompN( cDimName, sEle );
            WHILE( nComp > 0 );
                sComp = ElComp( cDimName, sEle, nComp );
                DimensionElementComponentDelete( cDimName, sEle, sComp );
                nComp = nComp - 1;
            END;
        ENDIF;
        nEleIdx = nEleIdx + 1;
    END;

ENDIF;

#########################################################
## Insert / Ensure Attributes Exist
#########################################################
AttrInsert( cDimName, '', sCaptionAttr, 'A' );
AttrInsert( cDimName, '', sLongNameAttr, 'A' );
AttrInsert( cDimName, '', sNextPeriodAttr, 'S' );
AttrInsert( cDimName, '', sPrevPeriodAttr, 'S' );
AttrInsert( cDimName, '', sNextYearAttr, 'S' );
AttrInsert( cDimName, '', sPrevYearAttr, 'S' );
AttrInsert( cDimName, '', sLastPeriodAttr, 'S' );
AttrInsert( cDimName, '', sFirstPeriodAttr, 'S' );
AttrInsert( cDimName, '', sMonthActualsAttr, 'N' );
AttrInsert( cDimName, '', sYearNameAttr, 'S' );
AttrInsert( cDimName, '', sFinYearAttr, 'S' );
AttrInsert( cDimName, '', sMonthAttr, 'S' );
AttrInsert( cDimName, '', sDaysInPeriodAttr, 'N' );
AttrInsert( cDimName, '', sLeapYearAttr, 'N' );
AttrInsert( cDimName, '', sCalMonthNumAttr, 'N' );
AttrInsert( cDimName, '', sCalYearAttr, 'N' );
AttrInsert( cDimName, '', sStartSerialAttr, 'N' );
AttrInsert( cDimName, '', sEndSerialAttr, 'N' );

#########################################################
## Clear Existing Attribute Values
#########################################################
sAttributeCube = '}ElementAttributes_' | cDimName;
CubeClearData( sAttributeCube );

#########################################################
## Insert Top-Level Structural Elements
#########################################################
DimensionElementInsert( cDimName, '', sTopConsol, 'C' );

DimensionElementInsert( cDimName, '', sRepConsol, 'C' );
DimensionElementComponentAdd( cDimName, sTopConsol, sRepConsol, 0 );

DimensionElementInsert( cDimName, '', sSysConsol, 'C' );
DimensionElementComponentAdd( cDimName, sTopConsol, sSysConsol, 0 );

DimensionElementInsert( cDimName, '', sFYConsol, 'C' );
DimensionElementComponentAdd( cDimName, sRepConsol, sFYConsol, 1 );

DimensionElementInsert( cDimName, '', sQTRConsol, 'C' );
DimensionElementComponentAdd( cDimName, sRepConsol, sQTRConsol, 1 );

DimensionElementInsert( cDimName, '', sYTDConsol, 'C' );
DimensionElementComponentAdd( cDimName, sRepConsol, sYTDConsol, 1 );

DimensionElementInsert( cDimName, '', sYTGConsol, 'C' );
DimensionElementComponentAdd( cDimName, sRepConsol, sYTGConsol, 1 );

DimensionElementInsert( cDimName, '', sLTDConsol, 'C' );
DimensionElementComponentAdd( cDimName, sRepConsol, sLTDConsol, 1 );

IF( pIncludeDriverElement @= 'Y' );
    DimensionElementInsert( cDimName, '', sDriverConsol, 'C' );
    DimensionElementComponentAdd( cDimName, sRepConsol, sDriverConsol, 1 );
ENDIF;
IF( pIncludeInputElement @= 'Y' );
    DimensionElementInsert( cDimName, '', sInputConsol, 'C' );
    DimensionElementComponentAdd( cDimName, sRepConsol, sInputConsol, 1 );
ENDIF;

DimensionElementInsert( cDimName, '', sNoElement, 'N' );
DimensionElementComponentAdd( cDimName, sSysConsol, sNoElement, 1 );

#########################################################
## Build Temporary Month Lookup Control Dimension
## Used to resolve calendar month name, long name,
## day counts, and next/prev month for any FY start month
#########################################################
sMonthLookupDim = '}' | cDimName | '_MonthLookup';

IF( DimensionExists( sMonthLookupDim ) = 1 );
    DimensionDestroy( sMonthLookupDim );
ENDIF;

DimensionCreate( sMonthLookupDim );

# Attributes on the lookup dimension
AttrInsert( sMonthLookupDim, '', sNextPeriodAttr, 'S' );
AttrInsert( sMonthLookupDim, '', sPrevPeriodAttr, 'S' );
AttrInsert( sMonthLookupDim, '', sLongNameAttr, 'S' );
AttrInsert( sMonthLookupDim, '', sDaysInPeriodAttr, 'N' );
# LeapDays stores the day count for this month in a leap year (only Feb differs)
AttrInsert( sMonthLookupDim, '', 'Leap Days', 'N' );
AttrInsert( sMonthLookupDim, '', sCalMonthNumAttr, 'N' );

# Insert Jan - Dec, then Jan1 - Dec1 (second cycle for non-Jan FY start)
# The "1" suffix elements represent the same month names but in the
# second calendar year spanned by a non-January fiscal year
DimensionElementInsertDirect( sMonthLookupDim, '', 'Jan', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Feb', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Mar', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Apr', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'May', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Jun', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Jul', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Aug', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Sep', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Oct', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Nov', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Dec', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Jan1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Feb1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Mar1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Apr1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'May1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Jun1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Jul1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Aug1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Sep1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Oct1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Nov1', 'N' );
DimensionElementInsertDirect( sMonthLookupDim, '', 'Dec1', 'N' );

# Populate Next Period, Prev Period, Long Name, Standard Days, Leap Days, Cal Month Number
# Standard days = non-leap year day count
AttrPutS( 'Feb', sMonthLookupDim, 'Jan', sNextPeriodAttr ); AttrPutS( 'Dec', sMonthLookupDim, 'Jan', sPrevPeriodAttr ); AttrPutS( 'January', sMonthLookupDim, 'Jan', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Jan', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Jan', 'Leap Days' ); AttrPutN( 1, sMonthLookupDim, 'Jan', sCalMonthNumAttr );
AttrPutS( 'Mar', sMonthLookupDim, 'Feb', sNextPeriodAttr ); AttrPutS( 'Jan', sMonthLookupDim, 'Feb', sPrevPeriodAttr ); AttrPutS( 'February', sMonthLookupDim, 'Feb', sLongNameAttr ); AttrPutN( 28, sMonthLookupDim, 'Feb', sDaysInPeriodAttr ); AttrPutN( 29, sMonthLookupDim, 'Feb', 'Leap Days' ); AttrPutN( 2, sMonthLookupDim, 'Feb', sCalMonthNumAttr );
AttrPutS( 'Apr', sMonthLookupDim, 'Mar', sNextPeriodAttr ); AttrPutS( 'Feb', sMonthLookupDim, 'Mar', sPrevPeriodAttr ); AttrPutS( 'March', sMonthLookupDim, 'Mar', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Mar', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Mar', 'Leap Days' ); AttrPutN( 3, sMonthLookupDim, 'Mar', sCalMonthNumAttr );
AttrPutS( 'May', sMonthLookupDim, 'Apr', sNextPeriodAttr ); AttrPutS( 'Mar', sMonthLookupDim, 'Apr', sPrevPeriodAttr ); AttrPutS( 'April', sMonthLookupDim, 'Apr', sLongNameAttr ); AttrPutN( 30, sMonthLookupDim, 'Apr', sDaysInPeriodAttr ); AttrPutN( 30, sMonthLookupDim, 'Apr', 'Leap Days' ); AttrPutN( 4, sMonthLookupDim, 'Apr', sCalMonthNumAttr );
AttrPutS( 'Jun', sMonthLookupDim, 'May', sNextPeriodAttr ); AttrPutS( 'Apr', sMonthLookupDim, 'May', sPrevPeriodAttr ); AttrPutS( 'May', sMonthLookupDim, 'May', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'May', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'May', 'Leap Days' ); AttrPutN( 5, sMonthLookupDim, 'May', sCalMonthNumAttr );
AttrPutS( 'Jul', sMonthLookupDim, 'Jun', sNextPeriodAttr ); AttrPutS( 'May', sMonthLookupDim, 'Jun', sPrevPeriodAttr ); AttrPutS( 'June', sMonthLookupDim, 'Jun', sLongNameAttr ); AttrPutN( 30, sMonthLookupDim, 'Jun', sDaysInPeriodAttr ); AttrPutN( 30, sMonthLookupDim, 'Jun', 'Leap Days' ); AttrPutN( 6, sMonthLookupDim, 'Jun', sCalMonthNumAttr );
AttrPutS( 'Aug', sMonthLookupDim, 'Jul', sNextPeriodAttr ); AttrPutS( 'Jun', sMonthLookupDim, 'Jul', sPrevPeriodAttr ); AttrPutS( 'July', sMonthLookupDim, 'Jul', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Jul', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Jul', 'Leap Days' ); AttrPutN( 7, sMonthLookupDim, 'Jul', sCalMonthNumAttr );
AttrPutS( 'Sep', sMonthLookupDim, 'Aug', sNextPeriodAttr ); AttrPutS( 'Jul', sMonthLookupDim, 'Aug', sPrevPeriodAttr ); AttrPutS( 'August', sMonthLookupDim, 'Aug', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Aug', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Aug', 'Leap Days' ); AttrPutN( 8, sMonthLookupDim, 'Aug', sCalMonthNumAttr );
AttrPutS( 'Oct', sMonthLookupDim, 'Sep', sNextPeriodAttr ); AttrPutS( 'Aug', sMonthLookupDim, 'Sep', sPrevPeriodAttr ); AttrPutS( 'September', sMonthLookupDim, 'Sep', sLongNameAttr ); AttrPutN( 30, sMonthLookupDim, 'Sep', sDaysInPeriodAttr ); AttrPutN( 30, sMonthLookupDim, 'Sep', 'Leap Days' ); AttrPutN( 9, sMonthLookupDim, 'Sep', sCalMonthNumAttr );
AttrPutS( 'Nov', sMonthLookupDim, 'Oct', sNextPeriodAttr ); AttrPutS( 'Sep', sMonthLookupDim, 'Oct', sPrevPeriodAttr ); AttrPutS( 'October', sMonthLookupDim, 'Oct', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Oct', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Oct', 'Leap Days' ); AttrPutN( 10, sMonthLookupDim, 'Oct', sCalMonthNumAttr );
AttrPutS( 'Dec', sMonthLookupDim, 'Nov', sNextPeriodAttr ); AttrPutS( 'Oct', sMonthLookupDim, 'Nov', sPrevPeriodAttr ); AttrPutS( 'November', sMonthLookupDim, 'Nov', sLongNameAttr ); AttrPutN( 30, sMonthLookupDim, 'Nov', sDaysInPeriodAttr ); AttrPutN( 30, sMonthLookupDim, 'Nov', 'Leap Days' ); AttrPutN( 11, sMonthLookupDim, 'Nov', sCalMonthNumAttr );
AttrPutS( 'Jan', sMonthLookupDim, 'Dec', sNextPeriodAttr ); AttrPutS( 'Nov', sMonthLookupDim, 'Dec', sPrevPeriodAttr ); AttrPutS( 'December', sMonthLookupDim, 'Dec', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Dec', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Dec', 'Leap Days' ); AttrPutN( 12, sMonthLookupDim, 'Dec', sCalMonthNumAttr );
# Duplicate set for the second-cycle months (Jan1-Dec1) - same values
AttrPutS( 'Feb', sMonthLookupDim, 'Jan1', sNextPeriodAttr ); AttrPutS( 'Dec', sMonthLookupDim, 'Jan1', sPrevPeriodAttr ); AttrPutS( 'January', sMonthLookupDim, 'Jan1', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Jan1', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Jan1', 'Leap Days' ); AttrPutN( 1, sMonthLookupDim, 'Jan1', sCalMonthNumAttr );
AttrPutS( 'Mar', sMonthLookupDim, 'Feb1', sNextPeriodAttr ); AttrPutS( 'Jan', sMonthLookupDim, 'Feb1', sPrevPeriodAttr ); AttrPutS( 'February', sMonthLookupDim, 'Feb1', sLongNameAttr ); AttrPutN( 28, sMonthLookupDim, 'Feb1', sDaysInPeriodAttr ); AttrPutN( 29, sMonthLookupDim, 'Feb1', 'Leap Days' ); AttrPutN( 2, sMonthLookupDim, 'Feb1', sCalMonthNumAttr );
AttrPutS( 'Apr', sMonthLookupDim, 'Mar1', sNextPeriodAttr ); AttrPutS( 'Feb', sMonthLookupDim, 'Mar1', sPrevPeriodAttr ); AttrPutS( 'March', sMonthLookupDim, 'Mar1', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Mar1', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Mar1', 'Leap Days' ); AttrPutN( 3, sMonthLookupDim, 'Mar1', sCalMonthNumAttr );
AttrPutS( 'May', sMonthLookupDim, 'Apr1', sNextPeriodAttr ); AttrPutS( 'Mar', sMonthLookupDim, 'Apr1', sPrevPeriodAttr ); AttrPutS( 'April', sMonthLookupDim, 'Apr1', sLongNameAttr ); AttrPutN( 30, sMonthLookupDim, 'Apr1', sDaysInPeriodAttr ); AttrPutN( 30, sMonthLookupDim, 'Apr1', 'Leap Days' ); AttrPutN( 4, sMonthLookupDim, 'Apr1', sCalMonthNumAttr );
AttrPutS( 'Jun', sMonthLookupDim, 'May1', sNextPeriodAttr ); AttrPutS( 'Apr', sMonthLookupDim, 'May1', sPrevPeriodAttr ); AttrPutS( 'May', sMonthLookupDim, 'May1', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'May1', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'May1', 'Leap Days' ); AttrPutN( 5, sMonthLookupDim, 'May1', sCalMonthNumAttr );
AttrPutS( 'Jul', sMonthLookupDim, 'Jun1', sNextPeriodAttr ); AttrPutS( 'May', sMonthLookupDim, 'Jun1', sPrevPeriodAttr ); AttrPutS( 'June', sMonthLookupDim, 'Jun1', sLongNameAttr ); AttrPutN( 30, sMonthLookupDim, 'Jun1', sDaysInPeriodAttr ); AttrPutN( 30, sMonthLookupDim, 'Jun1', 'Leap Days' ); AttrPutN( 6, sMonthLookupDim, 'Jun1', sCalMonthNumAttr );
AttrPutS( 'Aug', sMonthLookupDim, 'Jul1', sNextPeriodAttr ); AttrPutS( 'Jun', sMonthLookupDim, 'Jul1', sPrevPeriodAttr ); AttrPutS( 'July', sMonthLookupDim, 'Jul1', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Jul1', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Jul1', 'Leap Days' ); AttrPutN( 7, sMonthLookupDim, 'Jul1', sCalMonthNumAttr );
AttrPutS( 'Sep', sMonthLookupDim, 'Aug1', sNextPeriodAttr ); AttrPutS( 'Jul', sMonthLookupDim, 'Aug1', sPrevPeriodAttr ); AttrPutS( 'August', sMonthLookupDim, 'Aug1', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Aug1', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Aug1', 'Leap Days' ); AttrPutN( 8, sMonthLookupDim, 'Aug1', sCalMonthNumAttr );
AttrPutS( 'Oct', sMonthLookupDim, 'Sep1', sNextPeriodAttr ); AttrPutS( 'Aug', sMonthLookupDim, 'Sep1', sPrevPeriodAttr ); AttrPutS( 'September', sMonthLookupDim, 'Sep1', sLongNameAttr ); AttrPutN( 30, sMonthLookupDim, 'Sep1', sDaysInPeriodAttr ); AttrPutN( 30, sMonthLookupDim, 'Sep1', 'Leap Days' ); AttrPutN( 9, sMonthLookupDim, 'Sep1', sCalMonthNumAttr );
AttrPutS( 'Nov', sMonthLookupDim, 'Oct1', sNextPeriodAttr ); AttrPutS( 'Sep', sMonthLookupDim, 'Oct1', sPrevPeriodAttr ); AttrPutS( 'October', sMonthLookupDim, 'Oct1', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Oct1', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Oct1', 'Leap Days' ); AttrPutN( 10, sMonthLookupDim, 'Oct1', sCalMonthNumAttr );
AttrPutS( 'Dec', sMonthLookupDim, 'Nov1', sNextPeriodAttr ); AttrPutS( 'Oct', sMonthLookupDim, 'Nov1', sPrevPeriodAttr ); AttrPutS( 'November', sMonthLookupDim, 'Nov1', sLongNameAttr ); AttrPutN( 30, sMonthLookupDim, 'Nov1', sDaysInPeriodAttr ); AttrPutN( 30, sMonthLookupDim, 'Nov1', 'Leap Days' ); AttrPutN( 11, sMonthLookupDim, 'Nov1', sCalMonthNumAttr );
AttrPutS( 'Jan', sMonthLookupDim, 'Dec1', sNextPeriodAttr ); AttrPutS( 'Nov', sMonthLookupDim, 'Dec1', sPrevPeriodAttr ); AttrPutS( 'December', sMonthLookupDim, 'Dec1', sLongNameAttr ); AttrPutN( 31, sMonthLookupDim, 'Dec1', sDaysInPeriodAttr ); AttrPutN( 31, sMonthLookupDim, 'Dec1', 'Leap Days' ); AttrPutN( 12, sMonthLookupDim, 'Dec1', sCalMonthNumAttr );

#########################################################
## Insert Elements - Loop Years and Months
#########################################################
nMinYear = nStartYear;
nMaxYear = nEndYear;

WHILE( nMinYear <= nMaxYear );
    sMinYear = NumberToString( nMinYear );

    #----------------------------------------------------------
    ## LEAP YEAR DETECTION
    ## Rule: divisible by 4, EXCEPT centuries (div by 100)
    ##       UNLESS also divisible by 400
    #----------------------------------------------------------
    nIsLeapYear = 0;
    IF( Mod( nMinYear, 400 ) = 0 );
        nIsLeapYear = 1;
    ELSEIF( Mod( nMinYear, 4 ) = 0 );
        IF( Mod( nMinYear, 100 ) <> 0 );
            nIsLeapYear = 1;
        ENDIF;
    ENDIF;

    ## For a non-January FY, February falls in the PRIOR calendar year
    ## relative to the fiscal year label. We must also check that year.
    ## e.g. FY2025 starting Jul: Feb is in calendar year 2024
    IF( sStartMonth @<> 'Jan' );
        nCalYearForFebCheck = nMinYear - 1;
    ELSE;
        nCalYearForFebCheck = nMinYear;
    ENDIF;

    nIsLeapYearFeb = 0;
    IF( Mod( nCalYearForFebCheck, 400 ) = 0 );
        nIsLeapYearFeb = 1;
    ELSEIF( Mod( nCalYearForFebCheck, 4 ) = 0 );
        IF( Mod( nCalYearForFebCheck, 100 ) <> 0 );
            nIsLeapYearFeb = 1;
        ENDIF;
    ENDIF;

    #----------------------------------------------------------
    ## Insert FY-level Consolidation Elements
    #----------------------------------------------------------
    sYearFYConsol  = 'FY ' | sMinYear;
    sYearQTRConsol = 'FY ' | sMinYear | '-QTR';
    sYearYTDConsol = 'FY ' | sMinYear | '-YTD';
    sYearYTGConsol = 'FY ' | sMinYear | '-YTG';
    sYearLTDConsol = 'FY ' | sMinYear | '-LTD';

    DimensionElementInsert( cDimName, '', sYearFYConsol, 'C' );
    DimensionElementComponentAdd( cDimName, sFYConsol, sYearFYConsol, 1 );

    DimensionElementInsert( cDimName, '', sYearQTRConsol, 'C' );
    DimensionElementComponentAdd( cDimName, sQTRConsol, sYearQTRConsol, 1 );

    DimensionElementInsert( cDimName, '', sYearYTDConsol, 'C' );
    DimensionElementComponentAdd( cDimName, sYTDConsol, sYearYTDConsol, 1 );

    DimensionElementInsert( cDimName, '', sYearYTGConsol, 'C' );
    DimensionElementComponentAdd( cDimName, sYTGConsol, sYearYTGConsol, 1 );

    DimensionElementInsert( cDimName, '', sYearLTDConsol, 'C' );
    DimensionElementComponentAdd( cDimName, sLTDConsol, sYearLTDConsol, 1 );

    IF( pIncludeDriverElement @= 'Y' );
        sYearDriver = sMinYear | '-Driver';
        DimensionElementInsert( cDimName, '', sYearDriver, 'N' );
        DimensionElementComponentAdd( cDimName, sDriverConsol, sYearDriver, 1 );
    ENDIF;

    IF( pIncludeInputElement @= 'Y' );
        sYearInput = sMinYear | '-Input';
        DimensionElementInsert( cDimName, '', sYearInput, 'N' );
        DimensionElementComponentAdd( cDimName, sInputConsol, sYearInput, 1 );
    ENDIF;

    #----------------------------------------------------------
    ## Quarter Consolidations Q1 - Q4
    #----------------------------------------------------------
    nQTRLoop = 1;
    WHILE( nQTRLoop <= 4 );
        sQElement = 'FY ' | sMinYear | '-Q' | NumberToString( nQTRLoop );
        DimensionElementInsert( cDimName, '', sQElement, 'C' );
        DimensionElementComponentAdd( cDimName, sYearQTRConsol, sQElement, 1 );
        nQTRLoop = nQTRLoop + 1;
    END;

    #----------------------------------------------------------
    ## YTD Consolidations P01-YTD through P13-YTD
    #----------------------------------------------------------
    nYTDLoop = 1;
    WHILE( nYTDLoop <= 13 );
        IF( nYTDLoop < 10 );
            sYTDElement = 'FY ' | sMinYear | '-0' | NumberToString( nYTDLoop ) | '-YTD';
        ELSE;
            sYTDElement = 'FY ' | sMinYear | '-' | NumberToString( nYTDLoop ) | '-YTD';
        ENDIF;
        DimensionElementInsert( cDimName, '', sYTDElement, 'C' );
        DimensionElementComponentAdd( cDimName, sYearYTDConsol, sYTDElement, 1 );
        nYTDLoop = nYTDLoop + 1;
    END;

    #----------------------------------------------------------
    ## YTG Consolidations P01-YTG through P11-YTG
    ## (YTG is meaningless for P12/P13 so excluded)
    #----------------------------------------------------------
    nYTGLoop = 1;
    WHILE( nYTGLoop <= 11 );
        IF( nYTGLoop < 10 );
            sYTGElement = 'FY ' | sMinYear | '-0' | NumberToString( nYTGLoop ) | '-YTG';
        ELSE;
            sYTGElement = 'FY ' | sMinYear | '-' | NumberToString( nYTGLoop ) | '-YTG';
        ENDIF;
        DimensionElementInsert( cDimName, '', sYTGElement, 'C' );
        DimensionElementComponentAdd( cDimName, sYearYTGConsol, sYTGElement, 1 );
        nYTGLoop = nYTGLoop + 1;
    END;

    #----------------------------------------------------------
    ## LTD Consolidations P01-LTD through P13-LTD
    #----------------------------------------------------------
    nLTDLoop = 1;
    WHILE( nLTDLoop <= 13 );
        IF( nLTDLoop < 10 );
            sLTDElement = 'FY ' | sMinYear | '-0' | NumberToString( nLTDLoop ) | '-LTD';
        ELSE;
            sLTDElement = 'FY ' | sMinYear | '-' | NumberToString( nLTDLoop ) | '-LTD';
        ENDIF;
        DimensionElementInsert( cDimName, '', sLTDElement, 'C' );
        DimensionElementComponentAdd( cDimName, sYearLTDConsol, sLTDElement, 1 );
        nLTDLoop = nLTDLoop + 1;
    END;

    #----------------------------------------------------------
    ## N-Level Month Elements: P00 (Op Bal) through P13
    ## Insert element and wire up to all relevant consolidations
    #----------------------------------------------------------
    nMinMonth = 0;
    nMaxMonth = 13;

    WHILE( nMinMonth <= nMaxMonth );

        IF( nMinMonth < 10 );
            sElement = sMinYear | '-0' | NumberToString( nMinMonth );
        ELSE;
            sElement = sMinYear | '-' | NumberToString( nMinMonth );
        ENDIF;

        DimensionElementInsert( cDimName, '', sElement, 'N' );

        # FY: P01 - P12 only
        IF( nMinMonth >= 1 );
            IF( nMinMonth <= 12 );
                DimensionElementComponentAdd( cDimName, sYearFYConsol, sElement, 1 );
            ENDIF;
        ENDIF;

        # QTR: P01 - P12 only (quarters are groups of 3 fiscal periods)
        IF( nMinMonth >= 1 );
            IF( nMinMonth <= 3 );
                DimensionElementComponentAdd( cDimName, 'FY ' | sMinYear | '-Q1', sElement, 1 );
            ELSEIF( nMinMonth <= 6 );
                DimensionElementComponentAdd( cDimName, 'FY ' | sMinYear | '-Q2', sElement, 1 );
            ELSEIF( nMinMonth <= 9 );
                DimensionElementComponentAdd( cDimName, 'FY ' | sMinYear | '-Q3', sElement, 1 );
            ELSEIF( nMinMonth <= 12 );
                DimensionElementComponentAdd( cDimName, 'FY ' | sMinYear | '-Q4', sElement, 1 );
            ENDIF;
        ENDIF;

        # YTD: each YTD-N consolidation contains P01 through PN
        IF( nMinMonth >= 1 );
            nYTDLoop = nMinMonth;
            WHILE( nYTDLoop <= 13 );
                IF( nYTDLoop < 10 );
                    sParent = 'FY ' | sMinYear | '-0' | NumberToString( nYTDLoop ) | '-YTD';
                ELSE;
                    sParent = 'FY ' | sMinYear | '-' | NumberToString( nYTDLoop ) | '-YTD';
                ENDIF;
                DimensionElementComponentAdd( cDimName, sParent, sElement, 1 );
                nYTDLoop = nYTDLoop + 1;
            END;
        ENDIF;

        # YTG: each YTG-N consolidation contains P(N+1) through P12
        IF( nMinMonth >= 1 );
            IF( nMinMonth <= 12 );
                nYTGLoop = 1;
                WHILE( nYTGLoop <= nMinMonth - 1 );
                    IF( nYTGLoop < 10 );
                        sParent = 'FY ' | sMinYear | '-0' | NumberToString( nYTGLoop ) | '-YTG';
                    ELSE;
                        sParent = 'FY ' | sMinYear | '-' | NumberToString( nYTGLoop ) | '-YTG';
                    ENDIF;
                    DimensionElementComponentAdd( cDimName, sParent, sElement, 1 );
                    nYTGLoop = nYTGLoop + 1;
                END;
            ENDIF;
        ENDIF;

        # LTD: each LTD-N consolidation contains P00 through PN
        # LTD consolidations start at P01 (no FY YYYY-00-LTD exists)
        # P00 (Opening Balance) rolls into P01-LTD through P13-LTD
        IF( nMinMonth >= 0 );
            nLTDLoop = nMinMonth;
            IF( nLTDLoop < 1 );
                nLTDLoop = 1;
            ENDIF;
            WHILE( nLTDLoop <= 13 );
                IF( nLTDLoop < 10 );
                    sParent = 'FY ' | sMinYear | '-0' | NumberToString( nLTDLoop ) | '-LTD';
                ELSE;
                    sParent = 'FY ' | sMinYear | '-' | NumberToString( nLTDLoop ) | '-LTD';
                ENDIF;
                DimensionElementComponentAdd( cDimName, sParent, sElement, 1 );
                nLTDLoop = nLTDLoop + 1;
            END;
        ENDIF;

        nMinMonth = nMinMonth + 1;
    END;
    # END Month loop

    nMinYear = nMinYear + 1;
END;
# END Year loop

DimensionSortOrder( cDimName, 'ByInput', 'Ascending', 'ByHierarchy', 'Ascending' );
"""

METADATA = """
#****Begin: Generated Statements***
#****End: Generated Statements****"""

DATA = """
#****Begin: Generated Statements***
#****End: Generated Statements****"""

EPILOG = r"""
#****Begin: Generated Statements***
#****End: Generated Statements****

#########################################################
## EPILOG: Populate All Attribute Values
## Runs after Prolog has built the full element/hierarchy
## structure. All AttrPutS / AttrPutN calls live here.
#########################################################

nMinYear = nStartYear;
nMaxYear = nEndYear;

WHILE( nMinYear <= nMaxYear );
    sMinYear = NumberToString( nMinYear );

    #----------------------------------------------------------
    ## LEAP YEAR DETECTION (repeated in Epilog - no shared state)
    #----------------------------------------------------------
    nIsLeapYear = 0;
    IF( Mod( nMinYear, 400 ) = 0 );
        nIsLeapYear = 1;
    ELSEIF( Mod( nMinYear, 4 ) = 0 );
        IF( Mod( nMinYear, 100 ) <> 0 );
            nIsLeapYear = 1;
        ENDIF;
    ENDIF;

    ## Determine the calendar year in which February falls for this FY
    IF( sStartMonth @<> 'Jan' );
        nCalYearForFebCheck = nMinYear - 1;
    ELSE;
        nCalYearForFebCheck = nMinYear;
    ENDIF;

    nIsLeapYearFeb = 0;
    IF( Mod( nCalYearForFebCheck, 400 ) = 0 );
        nIsLeapYearFeb = 1;
    ELSEIF( Mod( nCalYearForFebCheck, 4 ) = 0 );
        IF( Mod( nCalYearForFebCheck, 100 ) <> 0 );
            nIsLeapYearFeb = 1;
        ENDIF;
    ENDIF;

    IF( pDebug @= 'Y' );
        LogOutput( 'INFO', 'META DATA GBL Period | Year: ' | sMinYear | ' | LeapYear: ' | NumberToString( nIsLeapYear ) );
    ENDIF;

    #----------------------------------------------------------
    ## FY Consolidation Attributes
    #----------------------------------------------------------
    sYearFYConsol = 'FY ' | sMinYear;
    AttrPutS( sMinYear | '-01', cDimName, sYearFYConsol, sFirstPeriodAttr );
    AttrPutS( sMinYear | '-12', cDimName, sYearFYConsol, sLastPeriodAttr );
    AttrPutS( NumberToString(nMinYear-1), cDimName, sYearFYConsol, sPrevYearAttr );
    AttrPutS( NumberToString(nMinYear+1), cDimName, sYearFYConsol, sNextYearAttr );
    AttrPutS( sMinYear, cDimName, sYearFYConsol, sCaptionAttr );
    AttrPutS( sMinYear, cDimName, sYearFYConsol, sYearNameAttr );
    AttrPutS( sMinYear, cDimName, sYearFYConsol, sFinYearAttr );
    AttrPutN( nIsLeapYear, cDimName, sYearFYConsol, sLeapYearAttr );

    #----------------------------------------------------------
    ## YTD Consolidation Attributes
    #----------------------------------------------------------
    sYearYTDConsol = 'FY ' | sMinYear | '-YTD';
    AttrPutS( sMinYear | '-01', cDimName, sYearYTDConsol, sFirstPeriodAttr );
    AttrPutS( sMinYear | '-13', cDimName, sYearYTDConsol, sLastPeriodAttr );
    AttrPutS( NumberToString(nMinYear-1), cDimName, sYearYTDConsol, sPrevYearAttr );
    AttrPutS( NumberToString(nMinYear+1), cDimName, sYearYTDConsol, sNextYearAttr );
    AttrPutS( sMinYear | '-YTD', cDimName, sYearYTDConsol, sCaptionAttr );
    AttrPutS( sMinYear, cDimName, sYearYTDConsol, sYearNameAttr );
    AttrPutN( nIsLeapYear, cDimName, sYearYTDConsol, sLeapYearAttr );

    #----------------------------------------------------------
    ## YTG Consolidation Attributes
    #----------------------------------------------------------
    sYearYTGConsol = 'FY ' | sMinYear | '-YTG';
    AttrPutS( sMinYear | '-01', cDimName, sYearYTGConsol, sFirstPeriodAttr );
    AttrPutS( sMinYear | '-13', cDimName, sYearYTGConsol, sLastPeriodAttr );
    AttrPutS( NumberToString(nMinYear-1), cDimName, sYearYTGConsol, sPrevYearAttr );
    AttrPutS( NumberToString(nMinYear+1), cDimName, sYearYTGConsol, sNextYearAttr );
    AttrPutS( sMinYear | '-YTG', cDimName, sYearYTGConsol, sCaptionAttr );
    AttrPutS( sMinYear, cDimName, sYearYTGConsol, sYearNameAttr );
    AttrPutN( nIsLeapYear, cDimName, sYearYTGConsol, sLeapYearAttr );

    #----------------------------------------------------------
    ## LTD Consolidation Attributes
    #----------------------------------------------------------
    sYearLTDConsol = 'FY ' | sMinYear | '-LTD';
    AttrPutS( sMinYear | '-00', cDimName, sYearLTDConsol, sFirstPeriodAttr );
    AttrPutS( sMinYear | '-13', cDimName, sYearLTDConsol, sLastPeriodAttr );
    AttrPutS( NumberToString(nMinYear-1), cDimName, sYearLTDConsol, sPrevYearAttr );
    AttrPutS( NumberToString(nMinYear+1), cDimName, sYearLTDConsol, sNextYearAttr );
    AttrPutS( sMinYear | '-LTD', cDimName, sYearLTDConsol, sCaptionAttr );
    AttrPutS( sMinYear, cDimName, sYearLTDConsol, sYearNameAttr );
    AttrPutN( nIsLeapYear, cDimName, sYearLTDConsol, sLeapYearAttr );

    #----------------------------------------------------------
    ## QTR Parent and Quarter-level Consolidation Attributes
    #----------------------------------------------------------
    sYearQTRConsol = 'FY ' | sMinYear | '-QTR';
    AttrPutS( sMinYear | '-QTR', cDimName, sYearQTRConsol, sCaptionAttr );
    AttrPutS( sMinYear, cDimName, sYearQTRConsol, sYearNameAttr );

    nQTRLoop = 1;
    WHILE( nQTRLoop <= 4 );
        sQStr    = NumberToString( nQTRLoop );
        sQElement = 'FY ' | sMinYear | '-Q' | sQStr;
        nComponents = ElCompN( cDimName, sQElement );
        sFirstAttr  = ElComp( cDimName, sQElement, 1 );
        sLastAttr   = ElComp( cDimName, sQElement, nComponents );
        AttrPutS( sFirstAttr, cDimName, sQElement, sFirstPeriodAttr );
        AttrPutS( sLastAttr, cDimName, sQElement, sLastPeriodAttr );
        AttrPutS( NumberToString(nMinYear-1), cDimName, sQElement, sPrevYearAttr );
        AttrPutS( NumberToString(nMinYear+1), cDimName, sQElement, sNextYearAttr );
        AttrPutS( sMinYear | '-Q' | sQStr, cDimName, sQElement, sCaptionAttr );
        AttrPutS( 'Quarter ' | sQStr | ' ' | sMinYear, cDimName, sQElement, sLongNameAttr );
        AttrPutS( sMinYear, cDimName, sQElement, sYearNameAttr );
        AttrPutN( nIsLeapYear, cDimName, sQElement, sLeapYearAttr );
        nQTRLoop = nQTRLoop + 1;
    END;

    #----------------------------------------------------------
    ## YTD Period Consolidation Attributes (FY YYYY-01-YTD etc)
    #----------------------------------------------------------
    nYTDLoop = 1;
    WHILE( nYTDLoop <= 13 );
        IF( nYTDLoop < 10 );
            sParent = 'FY ' | sMinYear | '-0' | NumberToString( nYTDLoop ) | '-YTD';
        ELSE;
            sParent = 'FY ' | sMinYear | '-' | NumberToString( nYTDLoop ) | '-YTD';
        ENDIF;
        nComponents = ElCompN( cDimName, sParent );
        AttrPutS( ElComp( cDimName, sParent, 1 ), cDimName, sParent, sFirstPeriodAttr );
        AttrPutS( ElComp( cDimName, sParent, nComponents ), cDimName, sParent, sLastPeriodAttr );
        AttrPutS( NumberToString(nMinYear-1), cDimName, sParent, sPrevYearAttr );
        AttrPutS( NumberToString(nMinYear+1), cDimName, sParent, sNextYearAttr );
        AttrPutS( sMinYear, cDimName, sParent, sYearNameAttr );
        AttrPutN( nIsLeapYear, cDimName, sParent, sLeapYearAttr );
        nYTDLoop = nYTDLoop + 1;
    END;

    #----------------------------------------------------------
    ## YTG Period Consolidation Attributes
    #----------------------------------------------------------
    nYTGLoop = 1;
    WHILE( nYTGLoop <= 11 );
        IF( nYTGLoop < 10 );
            sParent = 'FY ' | sMinYear | '-0' | NumberToString( nYTGLoop ) | '-YTG';
        ELSE;
            sParent = 'FY ' | sMinYear | '-' | NumberToString( nYTGLoop ) | '-YTG';
        ENDIF;
        nComponents = ElCompN( cDimName, sParent );
        AttrPutS( ElComp( cDimName, sParent, 1 ), cDimName, sParent, sFirstPeriodAttr );
        AttrPutS( ElComp( cDimName, sParent, nComponents ), cDimName, sParent, sLastPeriodAttr );
        AttrPutS( NumberToString(nMinYear-1), cDimName, sParent, sPrevYearAttr );
        AttrPutS( NumberToString(nMinYear+1), cDimName, sParent, sNextYearAttr );
        AttrPutS( sMinYear, cDimName, sParent, sYearNameAttr );
        AttrPutN( nIsLeapYear, cDimName, sParent, sLeapYearAttr );
        nYTGLoop = nYTGLoop + 1;
    END;

    #----------------------------------------------------------
    ## LTD Period Consolidation Attributes
    #----------------------------------------------------------
    nLTDLoop = 1;
    WHILE( nLTDLoop <= 13 );
        IF( nLTDLoop < 10 );
            sParent = 'FY ' | sMinYear | '-0' | NumberToString( nLTDLoop ) | '-LTD';
        ELSE;
            sParent = 'FY ' | sMinYear | '-' | NumberToString( nLTDLoop ) | '-LTD';
        ENDIF;
        nComponents = ElCompN( cDimName, sParent );
        AttrPutS( ElComp( cDimName, sParent, 1 ), cDimName, sParent, sFirstPeriodAttr );
        AttrPutS( ElComp( cDimName, sParent, nComponents ), cDimName, sParent, sLastPeriodAttr );
        AttrPutS( NumberToString(nMinYear-1), cDimName, sParent, sPrevYearAttr );
        AttrPutS( NumberToString(nMinYear+1), cDimName, sParent, sNextYearAttr );
        AttrPutS( sMinYear, cDimName, sParent, sYearNameAttr );
        AttrPutN( nIsLeapYear, cDimName, sParent, sLeapYearAttr );
        nLTDLoop = nLTDLoop + 1;
    END;

    #----------------------------------------------------------
    ## N-Level Element Attributes: P00 through P13
    #----------------------------------------------------------
    nMinMonth = 0;
    nMaxMonth = 13;

    WHILE( nMinMonth <= nMaxMonth );

        IF( nMinMonth < 10 );
            sElement = sMinYear | '-0' | NumberToString( nMinMonth );
        ELSE;
            sElement = sMinYear | '-' | NumberToString( nMinMonth );
        ENDIF;

        ## Year navigation attributes (all periods)
        AttrPutS( 'FY ' | sMinYear, cDimName, sElement, sFinYearAttr );
        AttrPutS( sMinYear, cDimName, sElement, sYearNameAttr );
        AttrPutS( NumberToString(nMinYear+1), cDimName, sElement, sNextYearAttr );
        AttrPutS( NumberToString(nMinYear-1), cDimName, sElement, sPrevYearAttr );
        AttrPutN( nIsLeapYear, cDimName, sElement, sLeapYearAttr );

        ## Next Period (P12 wraps to next year P01; P00 and P13 get no next)
        IF( nMinMonth = 12 );
            AttrPutS( NumberToString(nMinYear+1) | '-01', cDimName, sElement, sNextPeriodAttr );
        ELSEIF( nMinMonth >= 1 );
            IF( nMinMonth <= 11 );
                nNextMonth = nMinMonth + 1;
                IF( nNextMonth < 10 );
                    AttrPutS( sMinYear | '-0' | NumberToString(nNextMonth), cDimName, sElement, sNextPeriodAttr );
                ELSE;
                    AttrPutS( sMinYear | '-' | NumberToString(nNextMonth), cDimName, sElement, sNextPeriodAttr );
                ENDIF;
            ENDIF;
        ENDIF;

        ## Previous Period (P01 wraps to prior year P12; P00 and P13 get no prev)
        IF( nMinMonth = 1 );
            AttrPutS( NumberToString(nMinYear-1) | '-12', cDimName, sElement, sPrevPeriodAttr );
        ELSEIF( nMinMonth >= 2 );
            IF( nMinMonth <= 12 );
                nPrevMonth = nMinMonth - 1;
                IF( nPrevMonth < 10 );
                    AttrPutS( sMinYear | '-0' | NumberToString(nPrevMonth), cDimName, sElement, sPrevPeriodAttr );
                ELSE;
                    AttrPutS( sMinYear | '-' | NumberToString(nPrevMonth), cDimName, sElement, sPrevPeriodAttr );
                ENDIF;
            ENDIF;
        ENDIF;

        ##------------------------------------------------------
        ## Caption, Long Name, Month, Calendar Year,
        ## Days in Period, and Calendar Month Number
        ##------------------------------------------------------

        IF( nMinMonth = 0 );
            #-- P00: Opening Balance
            ## OB caption shows the prior calendar year e.g. OB-24
            nOpYear     = nMinYear - 1;
            sOpYearShort = SubSt( NumberToString(nOpYear), 3, 2 );
            AttrPutS( 'OB-' | sOpYearShort, cDimName, sElement, sCaptionAttr );
            AttrPutS( 'Opening Balance ' | NumberToString(nOpYear), cDimName, sElement, sLongNameAttr );
            AttrPutN( 0, cDimName, sElement, sDaysInPeriodAttr );
            AttrPutN( nOpYear, cDimName, sElement, sCalYearAttr );
            AttrPutN( 0, cDimName, sElement, sStartSerialAttr );
            AttrPutN( 0, cDimName, sElement, sEndSerialAttr );

        ELSEIF( nMinMonth = 13 );
            #-- P13: Period 13 adjustment period
            sYearShort = SubSt( sMinYear, 3, 2 );
            AttrPutS( 'P13-' | sYearShort, cDimName, sElement, sCaptionAttr );
            AttrPutS( 'Period 13 ' | sMinYear, cDimName, sElement, sLongNameAttr );
            AttrPutN( 0, cDimName, sElement, sDaysInPeriodAttr );
            AttrPutN( nMinYear, cDimName, sElement, sCalYearAttr );
            AttrPutN( 0, cDimName, sElement, sStartSerialAttr );
            AttrPutN( 0, cDimName, sElement, sEndSerialAttr );

            ## Set caption on P13-YTD and P13-LTD parents
            sParentYTD = 'FY ' | sMinYear | '-13-YTD';
            sParentLTD = 'FY ' | sMinYear | '-13-LTD';
            AttrPutS( 'P13-' | sYearShort | ' YTD', cDimName, sParentYTD, sCaptionAttr );
            AttrPutS( 'Period 13 ' | sMinYear | ' YTD', cDimName, sParentYTD, sLongNameAttr );
            AttrPutS( 'P13-' | sYearShort | ' LTD', cDimName, sParentLTD, sCaptionAttr );
            AttrPutS( 'Period 13 ' | sMinYear | ' LTD', cDimName, sParentLTD, sLongNameAttr );

        ELSE;
            #-- P01 through P12: Regular fiscal periods
            ## Resolve which calendar month this fiscal period maps to
            ## by indexing into the MonthLookup dimension from the FY start month
            nLookupIdx    = DimIx( sMonthLookupDim, sStartMonth ) + nMinMonth - 1;
            sCalMonthCode = SubSt( DimNm( sMonthLookupDim, nLookupIdx ), 1, 3 );
            sLongMonthName = AttrS( sMonthLookupDim, sCalMonthCode, sLongNameAttr );
            nCalMonthNum  = AttrN( sMonthLookupDim, sCalMonthCode, sCalMonthNumAttr );

            ## Determine the actual calendar year for this period
            ## Periods mapping to months >= start month are in the PRIOR calendar year
            ## (for non-Jan FY starts); periods mapping to months after the year boundary
            ## fall in the FY label year.
            IF( sStartMonth @= 'Jan' );
                nCalYear = nMinYear;
            ELSE;
                ## If the lookup index <= 12, the month is in the first calendar year of the FY
                ## (i.e. the year BEFORE the FY label)
                IF( nLookupIdx <= 12 );
                    nCalYear = nMinYear - 1;
                ELSE;
                    nCalYear = nMinYear;
                ENDIF;
            ENDIF;

            sCalYearShort = SubSt( NumberToString(nCalYear), 3, 2 );

            ## Caption: e.g. Jul-24, Aug-24 ...
            sCaption = sCalMonthCode | '-' | sCalYearShort;
            AttrPutS( sCaption, cDimName, sElement, sCaptionAttr );
            AttrPutS( sCalMonthCode, cDimName, sElement, sMonthAttr );
            AttrPutS( sLongMonthName | ' ' | NumberToString(nCalYear), cDimName, sElement, sLongNameAttr );
            AttrPutN( nCalMonthNum, cDimName, sElement, sCalMonthNumAttr );
            AttrPutN( nCalYear, cDimName, sElement, sCalYearAttr );

            ##----------------------------------------------------
            ## DAYS IN PERIOD with Leap Year awareness
            ## February gets 29 days if the CALENDAR year it falls
            ## in (nCalYear) is a leap year, not the FY label year
            ##----------------------------------------------------
            IF( sCalMonthCode @= 'Feb' );
                ## Check the actual calendar year Feb falls in
                nDaysInPeriod = 28;
                IF( Mod( nCalYear, 400 ) = 0 );
                    nDaysInPeriod = 29;
                ELSEIF( Mod( nCalYear, 4 ) = 0 );
                    IF( Mod( nCalYear, 100 ) <> 0 );
                        nDaysInPeriod = 29;
                    ENDIF;
                ENDIF;
            ELSE;
                nDaysInPeriod = AttrN( sMonthLookupDim, sCalMonthCode, sDaysInPeriodAttr );
            ENDIF;
            AttrPutN( nDaysInPeriod, cDimName, sElement, sDaysInPeriodAttr );

            ## Date Serials - pure arithmetic, no DayNo string dependency
            ## Uses Julian Day Number formula converted to Excel/TM1 serial
            ## (days since 1899-12-30, same as Excel)

            ## --- Start Serial: 1st day of month ---
            nSY = nCalYear;
            nSM = nCalMonthNum;
            IF( nSM <= 2 );
                nSY = nSY - 1;
                nSM = nSM + 12;
            ENDIF;
            nSA = INT( nSY / 100 );
            nSB = 2 - nSA + INT( nSA / 4 );
            nStartSerial = INT( 365.25 * ( nSY + 4716 ) ) + INT( 30.6001 * ( nSM + 1 ) ) + 1 + nSB - 2415020;

            ## --- End Serial: last day of month (nDaysInPeriod is leap-year aware) ---
            nEY = nCalYear;
            nEM = nCalMonthNum;
            IF( nEM <= 2 );
                nEY = nEY - 1;
                nEM = nEM + 12;
            ENDIF;
            nEA = INT( nEY / 100 );
            nEB = 2 - nEA + INT( nEA / 4 );
            nEndSerial = INT( 365.25 * ( nEY + 4716 ) ) + INT( 30.6001 * ( nEM + 1 ) ) + nDaysInPeriod + nEB - 2415020;

            AttrPutN( nStartSerial, cDimName, sElement, sStartSerialAttr );
            AttrPutN( nEndSerial, cDimName, sElement, sEndSerialAttr );

            ## Set Caption/LongName on YTD, YTG, LTD parent for this period
            sParentYTD = 'FY ' | sMinYear | '-' | SubSt(sElement, Long(sMinYear)+2, 2) | '-YTD';
            sParentYTG = 'FY ' | sMinYear | '-' | SubSt(sElement, Long(sMinYear)+2, 2) | '-YTG';
            sParentLTD = 'FY ' | sMinYear | '-' | SubSt(sElement, Long(sMinYear)+2, 2) | '-LTD';

            AttrPutS( sCaption | ' YTD', cDimName, sParentYTD, sCaptionAttr );
            AttrPutS( sLongMonthName | ' ' | NumberToString(nCalYear) | ' YTD', cDimName, sParentYTD, sLongNameAttr );

            IF( nMinMonth <= 11 );
                AttrPutS( sCaption | ' YTG', cDimName, sParentYTG, sCaptionAttr );
                AttrPutS( sLongMonthName | ' ' | NumberToString(nCalYear) | ' YTG', cDimName, sParentYTG, sLongNameAttr );
            ENDIF;

            AttrPutS( sCaption | ' LTD', cDimName, sParentLTD, sCaptionAttr );
            AttrPutS( sLongMonthName | ' ' | NumberToString(nCalYear) | ' LTD', cDimName, sParentLTD, sLongNameAttr );

        ENDIF;

        nMinMonth = nMinMonth + 1;
    END;
    # END Month attribute loop

    nMinYear = nMinYear + 1;
END;
# END Year attribute loop

#########################################################
## Clean Up Temporary Lookup Dimension
#########################################################
DimensionDestroy( sMonthLookupDim );

#########################################################
## Final Sort
#########################################################
DimensionSortOrder( cDimName, 'ByInput', 'Ascending', 'ByHierarchy', 'Ascending' );
"""


# ══════════════════════════════════════════════════════════════════════════════
# Build the JSON structure
# ══════════════════════════════════════════════════════════════════════════════

process = {
    "Name": PROCESS_NAME,
    "DataSource": {
        "Type": "None"
    },
    "Parameters": [
        {"Name": "pStartYear",            "Type": "String", "Value": "2011", "Prompt": "Start Year (YYYY)"},
        {"Name": "pEndYear",              "Type": "String", "Value": "2040", "Prompt": "End Year (YYYY)"},
        {"Name": "pStartMonth",           "Type": "String", "Value": "Jan",  "Prompt": "Fiscal Year Start Month (Jan, Feb, ... Dec)"},
        {"Name": "pPeriodDimName",        "Type": "String", "Value": "GBL Period", "Prompt": "Period Dimension Name"},
        {"Name": "pDeleteAndRebuild",     "Type": "String", "Value": "N",    "Prompt": "Delete and Rebuild dimension? (Y/N)"},
        {"Name": "pIncludeDriverElement", "Type": "String", "Value": "N",    "Prompt": "Include Driver Element per Year? (Y/N)"},
        {"Name": "pIncludeInputElement",  "Type": "String", "Value": "N",    "Prompt": "Include Input Element per Year? (Y/N)"},
        {"Name": "pDebug",                "Type": "String", "Value": "N",    "Prompt": "Enable Debug Logging? (Y/N)"},
    ],
    "Variables": [],
    "PrologProcedure":   PROLOG,
    "MetadataProcedure": METADATA,
    "DataProcedure":     DATA,
    "EpilogProcedure":   EPILOG,
}


# ══════════════════════════════════════════════════════════════════════════════
# Write JSON
# ══════════════════════════════════════════════════════════════════════════════

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(process, f, indent=2, ensure_ascii=False)

print(f"Written : {OUTPUT_FILE}")
print(f"Size    : {os.path.getsize(OUTPUT_FILE):,} bytes")
print(f"Process : {PROCESS_NAME}")
print(f"Default pPeriodDimName : GBL Period")
print()
print("Next step: run create_ti_meta_data_gbl_period.py to deploy and execute.")
