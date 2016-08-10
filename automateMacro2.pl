#!perl -w
use strict;
use warnings;
use Win32::OLE;
# Pass the full path of the spreadsheet 
# in the command line
my ($excel) = @ARGV;
print $excel."\n";
  my $ex;
        # use existing instance if Excel is already running
        eval { $ex = Win32::OLE->GetActiveObject('Excel.Application')};
        die "Excel not installed" if $@;
        unless (defined $ex) {
           $ex = Win32::OLE->new('Excel.Application', sub {$_[0]->Quit;})
                    or die "Oops, cannot start Excel";
        }
	my $xlbook = $ex->Workbooks->open($excel,0,"False")
	                or die "Error opening file ".$excel;

	#Call macro that will refresh any data source as
    #well as the pivot tables using the ActiveWorksheet.RefreshAll
    # This works with a Macro enabled workbook
	$ex->Run("RefreshTables");
	$xlbook->Close(1);
	$ex->Quit();
	
	print "Finished refreshing"