import { api } from '../apiClient';
import { DetectAnomaliesRequest, DetectAnomaliesResponse } from '../types';

export async function fetchAnomalies(data: DetectAnomaliesRequest, token: string): Promise<DetectAnomaliesResponse> {
  return api.detectAnomalies(data, token);
}
