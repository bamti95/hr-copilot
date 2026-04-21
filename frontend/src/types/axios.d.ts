import "axios";

declare module "axios" {
  interface AxiosRequestConfig<D = unknown> {
    skipGlobalLoading?: boolean;
    __globalLoadingTracked?: boolean;
  }

  interface InternalAxiosRequestConfig<D = unknown> {
    skipGlobalLoading?: boolean;
    __globalLoadingTracked?: boolean;
  }
}
