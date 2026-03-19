"""
create_json_ti_meta_data_gbl_version.py
Generates ti_meta_data_gbl_version.json — the TI process that reads
version attributes from GBL Version and populates GBL Assumptions period flags.

Single parameter: pVersion — the version to process.
All other settings are read from GBL Version attributes edited directly
in PAW via the }ElementAttributes_GBL Version cube:

  Is Snapshot             Y/N — if Y process aborts immediately
  Start Period            First active period e.g. 2025-04
  End Period              Last active period (used if Number of Rolling Months is 0)
  Number of Rolling Months If > 0, End Period is calculated automatically
                           by walking forward N periods from Start Period
"""

import json
import os

PROCESS_NAME = 'META DATA GBL Version'
JSON_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_files')
os.makedirs(JSON_DIR, exist_ok=True)
OUTPUT_FILE  = os.path.join(JSON_DIR, 'ti_meta_data_gbl_version.json')

PROLOG = r"""
#****Begin: Generated Statements***
#****End: Generated Statements****

#########################################################
## META DATA GBL Version
##
## Reads version settings from GBL Version attributes
## and populates GBL Assumptions period flags.
##
## Admin edits attributes directly in PAW via:
##   }ElementAttributes_GBL Version
##
## Parameter:
##   pVersion — version to process e.g. Actual
##
## Attributes read from GBL Version:
##   Is Snapshot             Y = abort, version is locked
##   Start Period            First active period
##   End Period              Last active period (if rolling months = 0)
##   Number of Rolling Months If > 0, calculate End Period automatically
#########################################################

cProcessName     = GetProcessName();
cVersionDim      = 'GBL Version';
cPeriodDim       = 'GBL Period';
cAssumptionsCube = 'GBL Assumptions';

#########################################################
## Validate pVersion
#########################################################
IF( DimIx( cVersionDim, pVersion ) = 0 );
    LogOutput( 'ERROR', cProcessName | ': pVersion ''' | pVersion | ''' not found in ' | cVersionDim );
    ProcessError;
ENDIF;

#########################################################
## Read settings from GBL Version attributes
#########################################################
sIsSnapshot      = ATTRS( cVersionDim, pVersion, 'Is Snapshot' );
sStartPeriod     = ATTRS( cVersionDim, pVersion, 'Start Period' );
sEndPeriod       = ATTRS( cVersionDim, pVersion, 'End Period' );
nRollingMonths   = ATTRN( cVersionDim, pVersion, 'Number of Rolling Months' );

LogOutput( 'INFO', cProcessName | ' | Version: '         | pVersion );
LogOutput( 'INFO', cProcessName | ' | Is Snapshot: '     | sIsSnapshot );
LogOutput( 'INFO', cProcessName | ' | Start Period: '    | sStartPeriod );
LogOutput( 'INFO', cProcessName | ' | End Period: '      | sEndPeriod );
LogOutput( 'INFO', cProcessName | ' | Rolling Months: '  | NumberToString( nRollingMonths ) );

#########################################################
## Snapshot check — abort if version is locked
#########################################################
IF( sIsSnapshot @= 'Y' );
    LogOutput( 'ERROR', cProcessName | ': Version ' | pVersion | ' is a Snapshot — aborting.' );
    ProcessError;
ENDIF;

#########################################################
## Validate Start Period
#########################################################
IF( sStartPeriod @= '' );
    LogOutput( 'ERROR', cProcessName | ': Start Period attribute is blank for ' | pVersion );
    ProcessError;
ENDIF;

IF( DimIx( cPeriodDim, sStartPeriod ) = 0 );
    LogOutput( 'ERROR', cProcessName | ': Start Period ''' | sStartPeriod | ''' not found in ' | cPeriodDim );
    ProcessError;
ENDIF;

#########################################################
## Calculate End Period
## If Number of Rolling Months > 0, walk forward N periods
## from Start Period using the Next Period attribute.
## Otherwise use End Period attribute directly.
#########################################################
IF( nRollingMonths > 0 );
    sCalcEndPeriod = sStartPeriod;
    nCount = 1;
    WHILE( nCount < nRollingMonths );
        sNextPeriod = ATTRS( cPeriodDim, sCalcEndPeriod, 'Next Period' );
        IF( sNextPeriod @= '' );
            LogOutput( 'ERROR', cProcessName | ': Next Period attribute is blank for ' | sCalcEndPeriod | ' — check GBL Period attributes.' );
            ProcessError;
        ENDIF;
        sCalcEndPeriod = sNextPeriod;
        nCount = nCount + 1;
    END;
    LogOutput( 'INFO', cProcessName | ' | Calculated End Period: ' | sCalcEndPeriod | ' (' | NumberToString( nRollingMonths ) | ' rolling months)' );
ELSE;
    IF( sEndPeriod @= '' );
        LogOutput( 'ERROR', cProcessName | ': End Period attribute is blank and Number of Rolling Months = 0 for ' | pVersion );
        ProcessError;
    ENDIF;
    IF( DimIx( cPeriodDim, sEndPeriod ) = 0 );
        LogOutput( 'ERROR', cProcessName | ': End Period ''' | sEndPeriod | ''' not found in ' | cPeriodDim );
        ProcessError;
    ENDIF;
    sCalcEndPeriod = sEndPeriod;
    LogOutput( 'INFO', cProcessName | ' | Using explicit End Period: ' | sCalcEndPeriod );
ENDIF;

# Write calculated End Period back to attribute
AttrPutS( sCalcEndPeriod, cVersionDim, pVersion, 'End Period' );

#########################################################
## Loop all leaf periods and set GBL Assumptions flags
#########################################################
nPeriodCount = DimSiz( cPeriodDim );
nPeriodIdx   = 1;

WHILE( nPeriodIdx <= nPeriodCount );
    sPeriod = DimNm( cPeriodDim, nPeriodIdx );

    # Only process leaf elements (level 0) — skip consolidations
    IF( ELLEV( cPeriodDim, sPeriod ) = 0 );

        nIsActive        = 0;
        nIsLocked        = 0;
        nIsCurrentPeriod = 0;

        # Active = period falls within Start to calculated End
        IF( sPeriod @>= sStartPeriod & sPeriod @<= sCalcEndPeriod );
            nIsActive = 1;
        ENDIF;

        # Locked = period is before Start (superseded by Actual)
        IF( sPeriod @< sStartPeriod );
            nIsLocked = 1;
        ENDIF;

        # Current period flag = calculated End Period only
        IF( sPeriod @= sCalcEndPeriod );
            nIsCurrentPeriod = 1;
        ENDIF;

        CellPutN( nIsActive,        cAssumptionsCube, pVersion, sPeriod, 'Is Active' );
        CellPutN( nIsLocked,        cAssumptionsCube, pVersion, sPeriod, 'Is Locked' );
        CellPutN( nIsCurrentPeriod, cAssumptionsCube, pVersion, sPeriod, 'Current Period Flag' );

    ENDIF;

    nPeriodIdx = nPeriodIdx + 1;
END;

LogOutput( 'INFO', cProcessName | ' | GBL Assumptions updated for ' | pVersion | ' | Start: ' | sStartPeriod | ' | End: ' | sCalcEndPeriod );
"""

METADATA = """
#****Begin: Generated Statements***
#****End: Generated Statements****"""

DATA = """
#****Begin: Generated Statements***
#****End: Generated Statements****"""

EPILOG = """
#****Begin: Generated Statements***
#****End: Generated Statements****"""

process = {
    "Name": PROCESS_NAME,
    "DataSource": {"Type": "None"},
    "Parameters": [
        {"Name": "pVersion", "Type": "String", "Value": "Actual", "Prompt": "Version to process e.g. Actual, Budget, Forecast"},
    ],
    "Variables":         [],
    "PrologProcedure":   PROLOG,
    "MetadataProcedure": METADATA,
    "DataProcedure":     DATA,
    "EpilogProcedure":   EPILOG,
}

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(process, f, indent=2, ensure_ascii=False)

print(f"Written : {OUTPUT_FILE}")
print(f"Process : {PROCESS_NAME}")
print(f"Params  : {len(process['Parameters'])} parameter (pVersion only)")
print()
print("Settings are read from GBL Version attributes in PAW:")
print("  }ElementAttributes_GBL Version")
print()
print("Next step: run create_ti_meta_data_gbl_version.py to deploy to TM1.")
