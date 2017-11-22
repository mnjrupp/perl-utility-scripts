#!perl -w
use strict;
use warnings;
use Win32::OLE;
use Win32::OLE::Const;
use Data::Dumper;
#package orders::webfetch;
#sub fetch {
      my $stat;
      my $BROWSER = Win32::OLE->new('InternetExplorer.Application');
	  
	  #Win32::OLE->WithEvents($BROWSER,\&Event,"DWebBrowserEvents2");
      # access the web site
      $BROWSER->{'Visible'}=1;
      $BROWSER->Navigate("webpage");
      
	 # Win32::OLE->MessageLoop();
      # wait until HTML page has loaded
       # do
       # {
             sleep(1);
              $stat=$BROWSER->{ReadyState};
			  #print Dumper($BROWSER);
			  print $stat . "\n";
       # }
       # while (!$stat);
	  
# sub Event {
    # my ($Obj,$Event,@Args) = @_;
    # print "Here is the Event: $Event\n";
    # if ($Event eq "DocumentComplete") {
       # my $IEObject = shift @Args;
        # my $doc=$IEObject->{Document};
	    # my $body = $doc->{body};
        # my $html = $body->{innerHTML};
		# print $html;
		
            # Win32::OLE->QuitMessageLoop();
    # }
# }
      #Win32::OLE->QuitMessageLoop();
      # get the HTML page from the browser
      my $doc=$BROWSER->{Document};
	    my $body = $doc->{body};
        my $html = $body->{innerHTML};
		print $html;
#}