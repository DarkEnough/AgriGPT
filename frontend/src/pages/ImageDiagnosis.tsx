import { useState, useEffect } from "react";
import { Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { askImage } from "@/api/agriApi";
import Loader from "@/components/Loader";
import { toast } from "sonner";

const ImageDiagnosis = () => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  /** Cleanup object URL on unmount */
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Please select a valid image file");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error("Image size must be less than 10MB");
      return;
    }

    setSelectedImage(file);

    // Cleanup previous URL
    if (previewUrl) URL.revokeObjectURL(previewUrl);

    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
  };

  const removeImage = () => {
    setSelectedImage(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setResult(null);
  };

  /** Better error extractor */
  const extractErrorMessage = (error: any) => {
    return (
      error?.response?.data?.detail ||
      error?.response?.data?.error ||
      error?.response?.data?.message ||
      error?.message ||
      "Failed to diagnose image"
    );
  };

  const handleDiagnose = async () => {
    if (!selectedImage) {
      toast.error("Please select an image first");
      return;
    }

    try {
      setIsLoading(true);
      const response = await askImage(selectedImage);
      setResult(response.response);
      toast.success("Diagnosis complete");
    } catch (error: any) {
      console.error("Diagnosis error:", error);
      toast.error(extractErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-background p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground mb-2">Image Diagnosis</h1>
          <p className="text-muted-foreground">
            Upload an image of your crop to detect pests, diseases, or other issues
          </p>
        </div>

        <Card className="p-6 space-y-6">
          {!previewUrl ? (
            <label className="flex flex-col items-center justify-center border-2 border-dashed border-border rounded-lg p-12 cursor-pointer hover:border-primary transition-colors">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                className="hidden"
              />
              <Upload className="w-16 h-16 text-muted-foreground mb-4" />
              <p className="text-lg font-medium text-foreground mb-2">Click to upload an image</p>
              <p className="text-sm text-muted-foreground">
                Supports: JPG, PNG, WEBP (max 10MB)
              </p>
            </label>
          ) : (
            <div className="space-y-4">
              <div className="relative">
                <img
                  src={previewUrl}
                  alt="Selected crop"
                  className="w-full max-h-96 object-contain rounded-lg border-2 border-primary shadow-lg"
                />
                <Button
                  size="icon"
                  variant="destructive"
                  className="absolute top-2 right-2"
                  onClick={removeImage}
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>

              {!result && !isLoading && (
                <Button onClick={handleDiagnose} className="w-full" size="lg">
                  Diagnose Image
                </Button>
              )}

              {isLoading && <Loader message="Analyzing your crop image..." />}

              {result && !isLoading && (
                <div className="bg-card border border-border rounded-lg p-6 space-y-3">
                  <h3 className="text-lg font-bold text-foreground">Diagnosis Result</h3>
                  <div className="text-card-foreground whitespace-pre-wrap">
                    {result.split("\n").map((line, i) => {
                      if (line.trim().startsWith("•") || line.trim().startsWith("-")) {
                        return (
                          <div key={i} className="ml-2 mb-1">
                            {line}
                          </div>
                        );
                      }
                      if (line.trim().endsWith(":") && line.trim().length < 50) {
                        return (
                          <div key={i} className="font-semibold mt-3 mb-1">
                            {line}
                          </div>
                        );
                      }
                      return <div key={i}>{line || "\u00A0"}</div>;
                    })}
                  </div>

                  <Button onClick={removeImage} variant="outline" className="w-full mt-4">
                    Analyze Another Image
                  </Button>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default ImageDiagnosis;
