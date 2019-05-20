function model(fsy_o,fsu_o,esu_o,fc, As1,As2,As3,Rr,P)

global NE

global colWidth
global colDepth

d1=42.5;
d2=79.5;
d3=160;
d4=110;
d5=50;

LL1=18600;
LL2=22800;
n=NE;
deadload1=P*LL1/20;
deadload2=P*LL2/20;

fc=-fc;
%pitting corrosion
D0= 25;% rebar dimension
i_corr= 2; % current density [microA/cm^2]
t=50; % time since corrosion initiation[year]
p= 0.0116*i_corr*Rr*t; %  maximum pit depth, Eq.2 [1][mm]
delta = p/D0;
delta_s=pen_depth_to_area_loss(delta);%reducton of As2
%delta_s=Ds;
if fsu_o<fsy_o
    fsu_o=fsy_o;
end
esu = esu_o*epsu_corr_BV(1, delta_s, 'pitting');
fsy = fsy_o*epsu_corr_L(1, 0, delta_s, 0.0016*100);
fsu = fsu_o*epsu_corr_L(1, 0, delta_s, 0.0026*100);
if fsu<fsy
    fsu=fsy;
end
As2 =As2*(1-delta_s);
As3 =As3*(1-delta_s);


%other factors
eshi=fsy/200e3;
eshi_o=fsy_o/200e3;
Y=-1000;
numIcr=2000;
dY=Y/numIcr;
% =========================================================================
% WRITE THE TCL FILE
% =========================================================================
os_dir  = 'C:\Users\jiangq\Desktop\code\continuous_beam\uniform\';
fname   = 'NewBeam.tcl';

fileID     = fopen([os_dir, '\', fname], 'w');
fprintf(fileID,'wipe'); 
fprintf(fileID,'\n\n');
fprintf(fileID,'model basic -ndm 2 -ndf 3');
fprintf(fileID,'\n\n');
fprintf(fileID,'geomTransf Linear 1');
fprintf(fileID,'\n\n');
% -------------------------------------------------------------------------
% MAT
% -------------------------------------------------------------------------
% .........................................................................
% concrete
% .........................................................................
%  fprintf(fileID,'uniaxialMaterial Concrete01 1 %.2e -0.0009 %.2e -0.0035',...
%             [fc, 0.8*fc]);
fprintf(fileID, 'uniaxialMaterial Concrete02  1  %.2e -0.002 %.2e -0.0035 0.5 0.0  47000',...
      [fc, 0.8*fc]);
 fprintf(fileID,'\n');

% .........................................................................
% rebar
% .........................................................................
 fprintf(fileID, 'uniaxialMaterial ElasticMultiLinear  2  -strain 0.0 %.5e %.5e 0.5  -stress  0.0  %.5e %.5e %.5e',...
     [eshi_o,esu_o, fsy_o, fsu_o, fsu_o]);
 fprintf(fileID,'\n\n'); 
fprintf(fileID, 'uniaxialMaterial ElasticMultiLinear  3  -strain 0.0 %.5e %.5e 0.5  -stress  0.0  %.5e %.5e %.5e',...
     [eshi,esu, fsy, fsu, fsu]);
 fprintf(fileID,'\n\n');
       
% -------------------------------------------------------------------------
% SECTION
% -------------------------------------------------------------------------
  y1=colDepth/2.0;
  z1=colWidth/2.0;
  for j=1:20
        sn=num2str(j);
         fprintf(fileID,['section Fiber ',sn,' {']);
         fprintf(fileID,'\n');
         fprintf(fileID,['patch rect 1 10 1',' [expr ',num2str(-y1),']  [expr ',num2str(-z1),']  ',num2str(y1),' ',num2str(z1)]);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  2  1  ',num2str(As1/2),' [expr ',num2str(y1-d1),']  0  [expr ',num2str(y1-d1),'] 0']);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  2  1  ',num2str(As1/2),' [expr ',num2str(y1-d2),']  0  [expr ',num2str(y1-d2),'] 0']);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  3   1  ',num2str(As3/3),' [expr ',num2str(d3-y1),'] 0 [expr ',num2str(d3-y1),'] 0']);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  3   1  ',num2str(As3/3),' [expr ',num2str(d4-y1),'] 0 [expr ',num2str(d4-y1),'] 0']);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  3   1  ',num2str(As3/3),' [expr ',num2str(d5-y1),'] 0 [expr ',num2str(d5-y1),'] 0']);

         fprintf(fileID,'\n}\n\n');
  end
  for j=21:42
        sn=num2str(j);
         fprintf(fileID,['section Fiber ',sn,' {']);
         fprintf(fileID,'\n');
         fprintf(fileID,['patch rect 1 10 1',' [expr ',num2str(-y1),']  [expr ',num2str(-z1),']  ',num2str(y1),' ',num2str(z1)]);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  2  1  ',num2str(As1/2),' [expr ',num2str(y1-d1),']  0  [expr ',num2str(y1-d1),'] 0']);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  2  1  ',num2str(As1/2),' [expr ',num2str(y1-d2),']  0  [expr ',num2str(y1-d2),'] 0']); 
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight 3 1  ',num2str(As2*5/11),' [expr ',num2str(d4-y1),'] 0 [expr ',num2str(d4-y1),'] 0']);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight 3 1  ',num2str(As2*6/11),' [expr ',num2str(d5-y1),'] 0 [expr ',num2str(d5-y1),'] 0']);
               fprintf(fileID,'\n}\n\n');
  end
  for j=43:62
        sn=num2str(j);
         fprintf(fileID,['section Fiber ',sn,' {']);
         fprintf(fileID,'\n');
         fprintf(fileID,['patch rect 1 10 1',' [expr ',num2str(-y1),']  [expr ',num2str(-z1),']  ',num2str(y1),' ',num2str(z1)]);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  2  1  ',num2str(As1/2),' [expr ',num2str(y1-d1),']  0  [expr ',num2str(y1-d1),'] 0']);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  2  1  ',num2str(As1/2),' [expr ',num2str(y1-d2),']  0  [expr ',num2str(y1-d2),'] 0']);        
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  3   1  ',num2str(As3/3),' [expr ',num2str(d3-y1),'] 0 [expr ',num2str(d3-y1),'] 0']);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  3   1  ',num2str(As3/3),' [expr ',num2str(d4-y1),'] 0 [expr ',num2str(d4-y1),'] 0']);
         fprintf(fileID,'\n');
         fprintf(fileID,['layer straight  3   1  ',num2str(As3/3),' [expr ',num2str(d5-y1),'] 0 [expr ',num2str(d5-y1),'] 0']); 
        fprintf(fileID,'\n}\n\n');
  end
% -------------------------------------------------------------------------
% NODES
% -------------------------------------------------------------------------
 for j=1:21
        sn=num2str(j);
        fprintf(fileID,['node ',sn,' ',num2str((j-1)*LL1/20),'  0.0']);
        fprintf(fileID,'\n');
 end
  for j=22:43
        sn=num2str(j);
        if j<=30
        fprintf(fileID,['node ',sn,' ',num2str(LL1+(j-21)*(LL2-3000)/18),'  0.0']);
        else
            if j>=34
        fprintf(fileID,['node ',sn,' ',num2str(LL1+LL2/2+1500+(j-34)*(LL2-3000)/18),'  0.0']);        
            else
            fprintf(fileID,['node ',sn,' ',num2str(LL1+LL2/2-1500+(j-30)*750),'  0.0']);        
            end
        end
        fprintf(fileID,'\n');
  end

  for j=44:63
        sn=num2str(j);
        fprintf(fileID,['node ',sn,' ',num2str(LL1+LL2+(j-43)*LL1/20),'  0.0']);
        fprintf(fileID,'\n');
 end
% -------------------------------------------------------------------------
% BC
% -------------------------------------------------------------------------
fprintf(fileID, 'fix 1  1 1 0'); 
fprintf(fileID,'\n');
fprintf(fileID, ['fix  ',num2str(21),'  0  1  0']); 
fprintf(fileID,'\n');
fprintf(fileID, ['fix  ',num2str(43),'  0  1  0']); 
fprintf(fileID,'\n');
fprintf(fileID, ['fix  ',num2str(63),'  0  1  0']); 
fprintf(fileID,'\n\n');

% -------------------------------------------------------------------------
% ELEMENT
% -------------------------------------------------------------------------
 for j=1:n
        sn=num2str(j);
        fprintf(fileID,['element  dispBeamColumn ',sn,' ',num2str(j),'  ',num2str(j+1),'  5  ',num2str(j),'  1']);
        fprintf(fileID,'\n');
 end
  fprintf(fileID,'\n\n');
% -------------------------------------------------------------------------
% DEAD LOAD
% -------------------------------------------------------------------------
fprintf(fileID,'pattern Plain 2 "Linear" {');
fprintf(fileID,'\n');
  for j=1:21
    fprintf(fileID,'load  %i 0.0 -%i 0.0',[j,deadload1/2]);
    fprintf(fileID,'\n');
  end
    for j=22:42
    fprintf(fileID,'load  %i 0.0 -%i 0.0',[j,deadload2/2]);
    fprintf(fileID,'\n');
    end
    for j=43:63
    fprintf(fileID,'load  %i 0.0 -%i 0.0',[j,deadload1/2]);
    fprintf(fileID,'\n');
  end
    fprintf(fileID,'}\n\n');
% -------------------------------------------------------------------------
% SOLVER OPTIONS
% -------------------------------------------------------------------------
fprintf(fileID,'system ProfileSPD'); 
fprintf(fileID,'\n');
fprintf(fileID,'numberer RCM'); 
fprintf(fileID,'\n');
fprintf(fileID,'constraints Plain'); 
fprintf(fileID,'\n');
fprintf(fileID,'test NormDispIncr 1.0e-3  50 3'); 
fprintf(fileID,'\n');
fprintf(fileID,'integrator LoadControl 1');
fprintf(fileID,'\n');
fprintf(fileID,'algorithm Newton'); 
fprintf(fileID,'\n');
fprintf(fileID,'analysis Static'); 
fprintf(fileID,'\n\n');
% -------------------------------------------------------------------------
% SOLVE
% -------------------------------------------------------------------------
fprintf(fileID, 'analyze 20'); 
fprintf(fileID,'\n\n');

% -------------------------------------------------------------------------
% LIVE LOAD
% -------------------------------------------------------------------------
fprintf(fileID, 'loadConst -time 0.0'); 
fprintf(fileID,'\n\n');
fprintf(fileID, 'pattern Plain 1  "Linear" {'); 
fprintf(fileID,'\n');
fprintf(fileID, ['load  ',num2str(n/2-1),' 0.0 -1.0 0.0']); 
fprintf(fileID,'\n');
fprintf(fileID, ['load  ',num2str(n/2+1),' 0.0 -1.0 0.0']); 
fprintf(fileID,'\n');
fprintf(fileID, ['load  ',num2str(n/2+3),' 0.0 -1.0 0.0']); 
fprintf(fileID,'\n}\n');
% -------------------------------------------------------------------------
% RECORDER
% -------------------------------------------------------------------------
fprintf(fileID, ['recorder Node -file section.out -time -node ',num2str(n/2+1),' -dof 2 disp']); 
fprintf(fileID,'\n');            
    
% -------------------------------------------------------------------------
% SOLVER OPTIONS
% -------------------------------------------------------------------------
fprintf(fileID,'system ProfileSPD'); 
fprintf(fileID,'\n');
fprintf(fileID,'numberer RCM'); 
fprintf(fileID,'\n');
fprintf(fileID,'constraints Plain'); 
fprintf(fileID,'\n');
fprintf(fileID,'test EnergyIncr 1.0e-3 500  5'); 
fprintf(fileID,'\n');
fprintf(fileID,['integrator DisplacementControl  ',num2str(n/2+1),'  2  ',num2str(dY)]);
fprintf(fileID,'\n');
fprintf(fileID,'algorithm Newton'); 
fprintf(fileID,'\n');
fprintf(fileID,'analysis Static'); 
fprintf(fileID,'\n\n');
% -------------------------------------------------------------------------
% SOLVE
% -------------------------------------------------------------------------
fprintf(fileID, 'set a 0'); 
fprintf(fileID,'\n');
fprintf(fileID, 'set b 0'); 
fprintf(fileID,'\n');
fprintf(fileID, 'set c 0'); 
fprintf(fileID,'\n');
fprintf(fileID, 'set d 0'); 
fprintf(fileID,'\n');
fprintf(fileID, 'set e 0'); 
fprintf(fileID,'\n');
fprintf(fileID, 'set f 0'); 
fprintf(fileID,'\n');
fprintf(fileID, 'set h 0'); 
fprintf(fileID,'\n');
fprintf(fileID, 'while { $a <= %i && $b <= %i && $c <= %i && $d <= %i && $e <= %i && $f <= %i && $h<=2000} {',[esu,esu,esu_o,esu_o,esu_o,esu_o]);
fprintf(fileID,'\n');
fprintf(fileID, 'analyze 1');
fprintf(fileID,'\n');
fprintf(fileID, ['set a [eleResponse ',num2str(n/2),' section 5 fiber -575 0 3 strain]']);
fprintf(fileID,'\n');
fprintf(fileID, ['set b [eleResponse ',num2str(n/2+1),' section 1 fiber -575 0 3 strain]']);
fprintf(fileID,'\n');
fprintf(fileID, ['set c [eleResponse ',num2str(20),' section 5 fiber 582.5 0 2 strain]']);
fprintf(fileID,'\n');
fprintf(fileID, ['set d [eleResponse ',num2str(21),' section 1 fiber 582.5 0 2 strain]']);
fprintf(fileID,'\n');
fprintf(fileID, ['set e [eleResponse ',num2str(42),' section 5 fiber 582.5 0 2 strain]']);
fprintf(fileID,'\n');
fprintf(fileID, ['set f [eleResponse ',num2str(43),' section 1 fiber 582.5 0 2 strain]']);
fprintf(fileID,'\n');
fprintf(fileID, 'set k [expr {$h+1}]');
 fprintf(fileID,'\n');
 fprintf(fileID, 'set h $k');
 fprintf(fileID,'\n');
fprintf(fileID, '}');
fprintf(fileID,'\n');

fclose(fileID);


