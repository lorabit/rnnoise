 ../wavutils/bin/wav2pcm noise.wav noise.pcm
../wavutils/bin/wav2pcm speech.wav speech.pcm
../src/denoise_training speech.pcm noise.pcm output.f32
../wavutils/bin/wav2pcm combine.wav combine.pcm &
python2 ../training/bin2hdf5.py output.f32 5000000 87 denoise_data9.h5
python2 ../training/rnn_train.py
python2 ../training/dump_rnn.py newweights9i.hdf5 ../src/rnn_data.c ../src/rnn_data.h
cd ../
make
cd wav
../examples/rnnoise_demo combine.pcm denoised.pcm
../wavutils/bin/pcm2wav 1 48000 16 denoised.pcm denoised.wav
