for d in m0316 m0256 m_tienich; do (cd $d && npx --yes hyperframes render --quality high -o ../$d.mp4 > ../$d.render.log 2>&1); done
echo ALLDONE
