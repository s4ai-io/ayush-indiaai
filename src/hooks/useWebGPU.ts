import { useState, useEffect } from 'react';
import { GPUInfo } from '@/types/voiceModel';

export function useWebGPU() {
  const [gpuInfo, setGpuInfo] = useState<GPUInfo>({
    supported: false,
    adapterName: null,
  });
  const [isDetecting, setIsDetecting] = useState(true);

  useEffect(() => {
    async function detectGPU() {
      try {
        if (!navigator.gpu) {
          setGpuInfo({
            supported: false,
            adapterName: null,
          });
          setIsDetecting(false);
          return;
        }

        const adapter = await navigator.gpu.requestAdapter();
        if (!adapter) {
          setGpuInfo({
            supported: false,
            adapterName: null,
          });
          setIsDetecting(false);
          return;
        }

        // Retrieve GPU details, handling API variance across browser versions
        let adapterInfo: any = null;
        if ('info' in adapter) {
          adapterInfo = (adapter as any).info;
        } else if (typeof (adapter as any).requestAdapterInfo === 'function') {
          adapterInfo = await (adapter as any).requestAdapterInfo();
        }

        setGpuInfo({
          supported: true,
          adapterName: adapterInfo?.description || adapterInfo?.device || 'Generic WebGPU Device',
          vendor: adapterInfo?.vendor || 'Unknown Vendor',
          architecture: adapterInfo?.architecture || 'Unknown Architecture',
        });
      } catch (error) {
        console.error('WebGPU detection error:', error);
        setGpuInfo({
          supported: false,
          adapterName: null,
        });
      } finally {
        setIsDetecting(false);
      }
    }

    detectGPU();
  }, []);

  return { gpuInfo, isDetecting };
}
