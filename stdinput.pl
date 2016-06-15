#!perl -w
#use strict;
use Switch;
use Data::Dumper;
use Win32::Console;
use Win32::Console::ANSI;
use Term::ANSIScreen qw/:color :cursor :screen :constants/;
use Term::Menu;
use vars qw(%CONFIG);

my @list = ("1 Item","2 Item","3 Item","4 Run sql file","5 List sql files");

%CONFIG = (
            sql_path => ".",
			sql_ext  => ".sql",
			);
			
my $out = new Win32::Console(STD_OUTPUT_HANDLE) || die;
    $out->Title("Help Menu");
my $buffer = new Win32::Console() || die;
my $attr = $out->Attr();

LOOP:$buffer->Cls();
     $buffer->Attr($FG_BLUE | $BG_GREEN);
     #$buffer->Cursor(10,0);
	
	 
	
	 &header;
	 $buffer->Attr($FG_GREEN | $BG_BLACK);
	 &menuitems;
	 $buffer->Attr($FG_BLUE | $BG_GREEN);
	 &cursorline;
	#$buffer->Display();
	
	 while(my $k = <STDIN>){
	   
		chomp($k);
	   
	   
	   my($x,$y) = $buffer->Cursor();
	   $buffer->Cursor($x+2,$y);
	   $buffer->Attr($FG_GREEN | $BG_BLACK);
	   switch($k){
		case 1		{$buffer->Write(&functoid1)}
		case 2		{$buffer->Write("2 was choosen")}
		case 4		{&runsql;}
		case 5		{&getSqlf;}
		else		{$buffer->Write("$k")}
	   
	   }
		&cursorline;
		$buffer->Attr($FG_BLUE | $BG_GREEN);
	   if($k eq 'q'){
		
		last;
	   }
	   
	  }
      &exitmenu;
     my $key = <STDIN>;
    chomp($key);
    goto LOOP if($key eq "n");
  
 $out->Display();
 #print "Welcome back to the original display!\n";
 undef $buffer;
 undef $out;
 
 sub functoid1{return 4*5;}
 
 sub header{
 #my $header = "";
  $buffer->FillChar("=", 70, 1, 1);
  $buffer->FillChar("|", 1, 1, 2);
  $buffer->Cursor(3,2);
  $buffer->Write("                               Menu                             ");
  $buffer->FillChar("|", 1, 70, 2);
  $buffer->FillChar("=", 70, 1, 3);
  $buffer->Cursor(6,10);
 
 }
 sub menuitems{
    my($x,$y) = $buffer->Cursor();
	for my $i (1..5){
	 $buffer->Cursor($x,$y++);
	 $buffer->Write("$list[$i-1]");
	 $buffer->Display();
	}
 
 }
 
 sub exitmenu{
	$buffer->Cursor(10,23);
	$buffer->Write("Do you want to quit?[Y/n] ");
	
 }
 
 sub cursorline{
		$buffer->Cursor(10,23);
		$buffer->Write("Enter menu # > ");
 
 }
 
 sub runsql{
		
		$buffer->FillChar(" ",50,1,23);
		$buffer->Cursor(10,23);
		$buffer->Write("Enter the sql file > ");
		my $file = <STDIN>;
		chomp($file);
		return $file;
 
 }
 sub getSqlf{
    
    opendir(my $dh,$CONFIG{'sql_path'}) || die "Can't open dir: $!"; 
	 my @files = grep{/$CONFIG{'sql_ext'}/} readdir ($dh);
	 $buffer->Cls();
	 &header;
	 foreach (@files){
	   $buffer->Write("$_ \n");
	 }
	 
 
 
 }